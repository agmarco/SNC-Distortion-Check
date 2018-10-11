from urllib.parse import urlparse

import pytest
from datetime import datetime
from django.contrib.auth.models import Permission
from django.urls import RegexURLPattern, reverse
from django.urls import RegexURLResolver
from django.conf import settings

from .. import factories
from ..urls import urlpatterns
from .view_config import VIEWS, Crud
from .utils import validate_create_view, validate_update_view, validate_delete_view, allowed_access, denied_access, \
    get_response

# import needed for side effect
from .fixtures import permissions_data, institution_data, http_method_data, license_data

TESTED_VIEWS = [view for view in VIEWS if not view.exclude]


def _view_data(view, user):
    if view.data is not None:
        return view.data(user)
    else:
        return None


def _patches(view):
    return view.patches if view.patches is not None else None


def _url(view, view_data=None):
    if callable(view.url):
        return view.url(view_data)
    else:
        return view.url


def _methods(view, view_data=None):
    for method, method_data in view.methods.items():
        if callable(method_data):
            method_data = method_data(view_data)
        yield method, method_data


def _get_views_from_urlpatterns(url_patterns):
    views = set()
    for pattern in url_patterns:
        if isinstance(pattern, RegexURLPattern):
            views.add(getattr(pattern.callback, 'view_class', pattern.callback))
        elif isinstance(pattern, RegexURLResolver):
            views.update(_get_views_from_urlpatterns(pattern.url_patterns))
    return views


def test_regression():
    """
    Test that each view used in the URLconf is tested.
    """
    views = _get_views_from_urlpatterns(urlpatterns)
    configured_views = set(view.view for view in VIEWS)
    unconfigured_view_names = [view.__name__ for view in views - configured_views]
    assert views == configured_views, f"The following views have no test configuration: {unconfigured_view_names}"


@pytest.mark.parametrize('view', (view for view in TESTED_VIEWS if not view.login_required))
@pytest.mark.django_db
def test_login_not_required(client, view):
    """
    For each public page, assert that visiting the view results in a 200 or a 302 redirect to something other than the
    login page.
    """
    view_data = _view_data(view, None)
    patches = _patches(view)
    url = _url(view, view_data)

    for method, method_data in _methods(view, view_data):
        response = get_response(client, url, method, method_data, patches)
        if response.status_code == 302:
            assert urlparse(response['Location']).path != reverse(settings.LOGIN_URL)
        else:
            assert response.status_code == 200


@pytest.mark.parametrize('view', (view for view in TESTED_VIEWS if view.login_required))
@pytest.mark.django_db
def test_login_required(client, view):
    """
    For each view that requires authentication, test that a user that is authenticated is granted access, and that a
    user that is not authenticated is either denied access or redirected to the login page.
    """

    johns_hopkins = factories.InstitutionFactory.create(name="Johns Hopkins")
    group = factories.GroupFactory.create(name="Group", permissions=Permission.objects.all())
    current_user = factories.UserFactory.create(email='current_user@johnshopkins.edu', institution=johns_hopkins, groups=[group])
    view_data = _view_data(view, current_user)
    patches = _patches(view)
    url = _url(view, view_data)

    for method, method_data in _methods(view, view_data):
        response = get_response(client, url, method, method_data, patches)
        if response.status_code == 302:
            assert urlparse(response['Location']).path == reverse(settings.LOGIN_URL)
        else:
            assert response.status_code == 403

    client.force_login(current_user)
    for method, method_data in _methods(view, view_data):
        assert allowed_access(client, url, method, method_data, patches)


@pytest.mark.parametrize('view', (view for view in TESTED_VIEWS if view.permissions))
def test_permissions(client, permissions_data, view):
    """
    For each view that requires some permission, test that a user that has the required permissions is granted access,
    and that a user that does not have the required permissions is denied access.
    """

    current_user = permissions_data['current_user']
    view_data = _view_data(view, current_user)
    patches = _patches(view)
    url = _url(view, view_data)

    client.force_login(current_user)

    if all(current_user.has_perm(permission) for permission in view.permissions):
        for method, method_data in _methods(view, view_data):
            assert allowed_access(client, url, method, method_data, patches)
    else:
        for method, method_data in _methods(view, view_data):
            assert denied_access(client, url, method, method_data, patches)


@pytest.mark.parametrize('view', (view for view in TESTED_VIEWS if view.validate_institution))
def test_institution(client, institution_data, view):
    """
    For each view that requires validation of the institution, test that a user that belongs to a matching institution
    is granted access, and that a user that does not belong to a matching institution is denied access.
    """

    current_user = institution_data['current_user']
    view_data = _view_data(view, current_user)
    patches = _patches(view)
    url = _url(view, view_data)

    client.force_login(current_user)

    if current_user.institution == institution_data['institution']:
        for method, method_data in _methods(view, view_data):
            assert allowed_access(client, url, method, method_data, patches)
    else:
        new_user = factories.UserFactory.create(
            email='new_user@example.com',
            institution=institution_data['institution'],
            groups=current_user.groups.all(),
        )
        client.force_login(new_user)
        for method, method_data in _methods(view, view_data):
            assert denied_access(client, url, method, method_data, patches)


@pytest.mark.parametrize('view', TESTED_VIEWS)
def test_http_methods(client, http_method_data, view):
    """
    For each view, test that the HTTP methods listed in the configuration dictionary are authorized,
    but the others aren't.
    """

    current_user = http_method_data['current_user']
    view_data = _view_data(view, current_user)
    patches = _patches(view)
    url = _url(view, view_data)
    method = http_method_data['method']

    client.force_login(current_user)

    if method in view.methods:
        method_data = view.methods[method]
        if callable(method_data):
            method_data = method_data(view_data)
        assert allowed_access(client, url, method, method_data, patches)
    else:
        assert denied_access(client, url, method, None, patches)


@pytest.mark.parametrize('view', (view for view in TESTED_VIEWS if view.crud is not None))
@pytest.mark.django_db
def test_crud(client, view):
    """
    For each view corresponding to a CREATE operation, test that a new model is created with the provided data.
    For each view corresponding to an UPDATE operation, test that the model is updated with the provided data.
    For each view corresponding to a DELETE operation, test that the model's 'deleted' attribute is set to True, but
    that no models are actually deleted.
    """

    johns_hopkins = factories.InstitutionFactory.create(name="Johns Hopkins")
    group = factories.GroupFactory.create(name="Group", permissions=Permission.objects.all())
    current_user = factories.UserFactory.create(email='current_user@johnshopkins.edu', institution=johns_hopkins, groups=[group])

    view_data = _view_data(view, current_user)
    patches = _patches(view)
    url = _url(view, view_data)
    operation, model, _ = view.crud
    post_data = view.crud[2](view_data) if callable(view.crud[2]) else view.crud[2]

    if operation == Crud.CREATE:
        validate_create_view(client, current_user, url, model, post_data, patches)
    elif operation == Crud.UPDATE:
        validate_update_view(client, current_user, url, model, post_data, patches)
    elif operation == Crud.DELETE:
        validate_delete_view(client, current_user, url, model, post_data, patches)


@pytest.mark.parametrize('view', TESTED_VIEWS)
def test_license(client, license_data, view):
    """
    If the view requires an unexpired license, check that an expired license makes the view
    inaccessible.
    If the view requires an scans remaining on the license, check that a license with no remaining
    scans makes the view inaccessible.
    """

    current_user = license_data['current_user']
    license_expiration_date = current_user.institution.license_expiration_date
    scans_remaining = current_user.institution.scans_remaining
    now = datetime.now().date()

    view_data = _view_data(view, current_user)
    patches = _patches(view)
    url = _url(view, view_data)

    client.force_login(current_user)

    if view.check_license or view.check_scans:
        if view.check_license:
            if license_expiration_date is not None and license_expiration_date <= now:
                for method, method_data in _methods(view, view_data):
                    assert denied_access(client, url, method, method_data, patches)
        elif view.check_scans:
            if scans_remaining == 0:
                for method, method_data in _methods(view, view_data):
                    assert denied_access(client, url, method, method_data, patches)
    else:
        for method, method_data in _methods(view, view_data):
            assert allowed_access(client, url, method, method_data, patches)

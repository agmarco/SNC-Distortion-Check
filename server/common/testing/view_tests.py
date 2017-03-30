import pytest
from urllib.parse import urlparse

from django.contrib.auth.models import Permission
from django.urls import RegexURLPattern, reverse
from django.urls import RegexURLResolver
from django.conf import settings

from .. import factories
from ..urls import urlpatterns
from .view_config import VIEWS, Crud
from .utils import validate_create_view, validate_update_view, validate_delete_view
from .fixtures import permissions_data, institution_data


def _get_view_names_from_urlpatterns(url_patterns):
    view_names = []
    for pattern in url_patterns:
        if isinstance(pattern, RegexURLPattern):
            view_names.append(pattern.callback.__name__)
        elif isinstance(pattern, RegexURLResolver):
            view_names.extend(_get_view_names_from_urlpatterns(pattern.url_patterns))
    return view_names


def _allowed_access(client, url, method, data):
    return getattr(client, method.lower())(url, data).status_code in (200, 302)


def _denied_access(client, url, method, data):
    return getattr(client, method.lower())(url, data).status_code == 403


def test_regression():
    """
    Test that each view used in the URLconf is tested.
    """

    view_names = set(_get_view_names_from_urlpatterns(urlpatterns))
    tested_view_names = set(view['view'].__name__ for view in VIEWS)
    assert view_names == tested_view_names, f"The following views are not tested: {view_names - tested_view_names}"


@pytest.mark.parametrize('view', (view for view in VIEWS if view['login_required']))
@pytest.mark.django_db
def test_login_required(client, view):
    """
    For each view that requires authentication, test that a user that is authenticated is granted access, and that a
    user that is not authenticated is either denied access or redirected to the login page.
    """

    johns_hopkins = factories.InstitutionFactory.create(name="Johns Hopkins")
    group = factories.GroupFactory.create(name="Group", permissions=Permission.objects.all())
    current_user = factories.UserFactory.create(username='current_user', institution=johns_hopkins, groups=[group])
    view_data = view['data'](current_user) if 'data' in view else None
    url = view['url'](view_data) if callable(view['url']) else view['url']

    for method, method_data in view['methods'].items():
        if callable(method_data):
            method_data = method_data(view_data)

        res = getattr(client, method.lower())(url, method_data)
        if res.status_code == 302:
            assert urlparse(res['Location']).path == reverse(settings.LOGIN_URL)
        else:
            assert res.status_code == 403

    client.force_login(current_user)
    for method, method_data in view['methods'].items():
        if callable(method_data):
            method_data = method_data(view_data)

        assert _allowed_access(client, url, method, method_data)


@pytest.mark.parametrize('view', (view for view in VIEWS if view['permissions']))
def test_permissions(client, permissions_data, view):
    """
    For each view that requires some permission, test that a user that has the required permissions is granted access,
    and that a user that does not have the required permissions is denied access.
    """

    current_user = permissions_data['current_user']
    view_data = view['data'](current_user) if 'data' in view else None
    url = view['url'](view_data) if callable(view['url']) else view['url']

    client.force_login(current_user)

    if all(current_user.has_perm(permission) for permission in view['permissions']):
        for method, method_data in view['methods'].items():
            if callable(method_data):
                method_data = method_data(view_data)
            assert _allowed_access(client, url, method, method_data)
    else:
        for method, method_data in view['methods'].items():
            if callable(method_data):
                method_data = method_data(view_data)
            assert _denied_access(client, url, method, method_data)


@pytest.mark.parametrize('view', (view for view in VIEWS if view['validate_institution']))
def test_institution(client, institution_data, view):
    """
    For each view that requires validation of the institution, test that a user that belongs to a matching institution
    is granted access, and that a user that does not belong to a matching institution is denied access.
    """

    current_user = institution_data['current_user']
    view_data = view['data'](current_user) if 'data' in view else None
    url = view['url'](view_data) if callable(view['url']) else view['url']

    client.force_login(current_user)

    if current_user.institution == institution_data['institution']:
        for method, method_data in view['methods'].items():
            if callable(method_data):
                method_data = method_data(view_data)
            assert _allowed_access(client, url, method, method_data)
    else:
        current_user.institution = institution_data['institution']
        current_user.save()
        for method, method_data in view['methods'].items():
            if callable(method_data):
                method_data = method_data(view_data)
            assert _denied_access(client, url, method, method_data)


@pytest.mark.parametrize('view', (view for view in VIEWS if 'crud' in view))
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
    current_user = factories.UserFactory.create(username='current_user', institution=johns_hopkins, groups=[group])

    view_data = view['data'](current_user) if 'data' in view else None
    url = view['url'](view_data) if callable(view['url']) else view['url']
    operation, model, _ = view['crud']
    post_data = view['crud'][2](view_data) if callable(view['crud'][2]) else view['crud'][2]

    if operation == Crud.CREATE:
        validate_create_view(client, current_user, url, model, post_data)
    elif operation == Crud.UPDATE:
        validate_update_view(client, current_user, url, model, post_data)
    elif operation == Crud.DELETE:
        validate_delete_view(client, current_user, url, model, post_data)

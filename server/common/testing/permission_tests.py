import pytest

import numpy as np

from django.test import Client
from django.urls import RegexURLPattern
from django.urls import RegexURLResolver
from django.urls import reverse
from django.contrib.auth.models import Permission

from .. import views
from .. import factories
from ..models import Global, GoldenFiducials
from ..urls import urlpatterns

VIEWS = (
    {
        'view': views.upload_file,
        'url': reverse('upload_file'),
        'permissions': ('common.configuration',),
        'validate_institution': False,
        'methods': ('GET', 'POST'),
    },
    {
        'view': views.configuration,
        'url': reverse('configuration'),
        'permissions': ('common.configuration',),
        'validate_institution': False,
        'methods': ('GET',),
    },
    {
        'view': views.CreatePhantom,
        'url': reverse('create_phantom'),
        'permissions': ('common.configuration',),
        'validate_institution': False,
        'methods': ('GET', 'POST'),
    },
    {
        'view': views.UpdatePhantom,
        'url': lambda data: reverse('update_phantom', args=(data['phantom'].pk,)),
        'permissions': ('common.configuration',),
        'validate_institution': True,
        'methods': ('GET', 'POST'),
    },
    {
        'view': views.DeletePhantom,
        'url': lambda data: reverse('delete_phantom', args=(data['phantom'].pk,)),
        'permissions': ('common.configuration',),
        'validate_institution': True,
        'methods': ('GET', 'POST'),
    },
    {
        'view': views.UploadCT,
        'url': lambda data: reverse('upload_ct', args=(data['phantom'].pk,)),
        'permissions': ('common.configuration',),
        'validate_institution': True,
        'methods': ('GET', 'POST'),
    },
    {
        'view': views.UploadRaw,
        'url': lambda data: reverse('upload_raw', args=(data['phantom'].pk,)),
        'permissions': ('common.configuration',),
        'validate_institution': True,
        'methods': ('GET', 'POST'),
    },
    {
        'view': views.DeleteGoldStandard,
        'url': lambda data: reverse('delete_gold_standard', args=(data['phantom'].pk, data['gold_standard'].pk)),
        'permissions': ('common.configuration',),
        'validate_institution': True,
        'methods': ('GET', 'POST'),
    },
    {
        'view': views.activate_gold_standard,
        'url': lambda data: reverse('activate_gold_standard', args=(data['phantom'].pk, data['gold_standard'].pk)),
        'permissions': ('common.configuration',),
        'validate_institution': True,
        'methods': ('POST',),
    },
    {
        'view': views.gold_standard_csv,
        'url': lambda data: reverse('gold_standard_csv', args=(data['phantom'].pk, data['gold_standard'].pk)),
        'permissions': ('common.configuration',),
        'validate_institution': True,
        'methods': ('GET',),
    },
    {
        'view': views.CreateMachine,
        'url': reverse('create_machine'),
        'permissions': ('common.configuration',),
        'validate_institution': False,
        'methods': ('GET', 'POST'),
    },
    {
        'view': views.UpdateMachine,
        'url': lambda data: reverse('update_machine', args=(data['machine'].pk,)),
        'permissions': ('common.configuration',),
        'validate_institution': True,
        'methods': ('GET', 'POST'),
    },
    {
        'view': views.DeleteMachine,
        'url': lambda data: reverse('delete_machine', args=(data['machine'].pk,)),
        'permissions': ('common.configuration',),
        'validate_institution': True,
        'methods': ('GET', 'POST'),
    },
    {
        'view': views.CreateSequence,
        'url': reverse('create_sequence'),
        'permissions': ('common.configuration',),
        'validate_institution': False,
        'methods': ('GET', 'POST'),
    },
    {
        'view': views.UpdateSequence,
        'url': lambda data: reverse('update_sequence', args=(data['sequence'].pk,)),
        'permissions': ('common.configuration',),
        'validate_institution': True,
        'methods': ('GET', 'POST'),
    },
    {
        'view': views.DeleteSequence,
        'url': lambda data: reverse('delete_sequence', args=(data['sequence'].pk,)),
        'permissions': ('common.configuration',),
        'validate_institution': True,
        'methods': ('GET', 'POST'),
    },
    {
        'view': views.CreateUser,
        'url': reverse('create_user'),
        'permissions': ('common.manage_users',),
        'validate_institution': False,
        'methods': ('GET', 'POST'),
    },
    {
        'view': views.UpdateUser,
        'url': lambda data: reverse('update_user', args=(data['user'].pk,)),
        'permissions': ('common.manage_users',),
        'validate_institution': True,
        'methods': ('GET', 'POST'),
    },
    {
        'view': views.DeleteUser,
        'url': lambda data: reverse('delete_user', args=(data['user'].pk,)),
        'permissions': ('common.manage_users',),
        'validate_institution': True,
        'methods': ('GET', 'POST'),
    },
)


@pytest.fixture(params=(None, *(permission[0] for permission in Global._meta.permissions)))
def permissions_data(db, request):
    group = factories.GroupFactory.create(name="Group")
    if request.param:
        group.permissions.add(Permission.objects.get(codename=request.param))

    johns_hopkins = factories.InstitutionFactory.create(name="Johns Hopkins")

    current_user = factories.UserFactory.create(
        username='username',
        institution=johns_hopkins,
        groups=[group],
    )

    user = factories.UserFactory.create(username='user', institution=johns_hopkins)
    phantom = factories.PhantomFactory(institution=johns_hopkins)
    machine = factories.MachineFactory(institution=johns_hopkins)
    sequence = factories.SequenceFactory(institution=johns_hopkins)
    fiducials = factories.FiducialsFactory(fiducials=np.zeros((5, 5)))
    gold_standard = factories.GoldenFiducialsFactory(phantom=phantom, type=GoldenFiducials.RAW, fiducials=fiducials)

    return {
        'current_user': current_user,
        'user': user,
        'phantom': phantom,
        'machine': machine,
        'sequence': sequence,
        'gold_standard': gold_standard,
    }


@pytest.fixture(params=(True, False))
def institution_data(db, request):
    johns_hopkins = factories.InstitutionFactory.create(name="Johns Hopkins")
    utexas = factories.InstitutionFactory.create(name="University of Texas")

    group = factories.GroupFactory.create(name="Group", permissions=Permission.objects.all())

    current_user = factories.UserFactory.create(
        username='username',
        institution=johns_hopkins if request.param else utexas,
        groups=[group],
    )

    user = factories.UserFactory.create(username='user', institution=johns_hopkins)
    phantom = factories.PhantomFactory(institution=johns_hopkins)
    machine = factories.MachineFactory(institution=johns_hopkins)
    sequence = factories.SequenceFactory(institution=johns_hopkins)
    fiducials = factories.FiducialsFactory(fiducials=np.zeros((5, 5)))
    gold_standard = factories.GoldenFiducialsFactory(phantom=phantom, type=GoldenFiducials.RAW, fiducials=fiducials)

    return {
        'current_user': current_user,
        'user': user,
        'phantom': phantom,
        'machine': machine,
        'sequence': sequence,
        'gold_standard': gold_standard,
        'institution': johns_hopkins,
    }


@pytest.mark.parametrize('view', VIEWS)
def test_permissions(permissions_data, view):
    current_user = permissions_data['current_user']
    url = view['url'](permissions_data) if callable(view['url']) else view['url']

    client = Client()
    client.force_login(current_user)

    if not view['permissions'] or all(current_user.has_perm(permission) for permission in view['permissions']):
        for method in view['methods']:
            assert getattr(client, method.lower())(url).status_code in (200, 302)
    else:
        for method in view['methods']:
            assert getattr(client, method.lower())(url).status_code == 403


@pytest.mark.parametrize('view', VIEWS)
def test_institution(institution_data, view):
    current_user = institution_data['current_user']
    url = view['url'](institution_data) if callable(view['url']) else view['url']

    client = Client()
    client.force_login(current_user)

    if not view['validate_institution'] or current_user.institution == institution_data['institution']:
        for method in view['methods']:
            assert getattr(client, method.lower())(url).status_code in (200, 302)
    else:
        for method in view['methods']:
            assert getattr(client, method.lower())(url).status_code == 403


def test_regression():
    view_names = set(_extract_view_names_from_urlpatterns(urlpatterns))
    tested_view_names = set(view['view'].__name__ for view in VIEWS)
    diff = view_names - tested_view_names
    assert not diff, f"The following views are not tested: {diff}"


def _extract_view_names_from_urlpatterns(url_patterns):
    view_names = []
    for pattern in url_patterns:
        if isinstance(pattern, RegexURLPattern):
            view_names.append(pattern.callback.__name__)
        elif isinstance(pattern, RegexURLResolver):
            view_names.extend(_extract_view_names_from_urlpatterns(pattern.url_patterns))
    return view_names

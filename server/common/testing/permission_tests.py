import pytest
from django.test import Client

from django.urls import reverse
from django.contrib.auth.models import Permission

from server.common import factories
from .utils import assert_can_view, assert_cannot_view


PERMISSIONS = (None, 'configuration', 'manage_users')

# This is a map of the permissions required for access to the different views.
VIEW_PERMISSIONS = {
    'login': {
        'permissions': (),
        'methods': ('GET',),
        'args': None,
    },
    'configuration': {
        'permissions': ('configuration',),
        'methods': ('GET',),
        'args': None,
    },
    'create_phantom': {
        'permissions': ('configuration',),
        'methods': ('GET', 'POST'),
        'args': None,
    },
    'update_phantom': {
        'permissions': ('configuration',),
        'methods': ('GET', 'POST'),
        'args': lambda data: (data['phantom'].pk,),
    },
    'delete_phantom': {
        'permissions': ('configuration',),
        'methods': ('GET', 'POST'),
        'args': lambda data: (data['phantom'].pk,),
    },
    'create_machine': {
        'permissions': ('configuration',),
        'methods': ('GET', 'POST'),
        'args': None,
    },
    'update_machine': {
        'permissions': ('configuration',),
        'methods': ('GET', 'POST'),
        'args': lambda data: (data['machine'].pk,),
    },
    'delete_machine': {
        'permissions': ('configuration',),
        'methods': ('GET', 'POST'),
        'args': lambda data: (data['machine'].pk,),
    },
    'create_sequence': {
        'permissions': ('configuration',),
        'methods': ('GET', 'POST'),
        'args': None,
    },
    'update_sequence': {
        'permissions': ('configuration',),
        'methods': ('GET', 'POST'),
        'args': lambda data: (data['sequence'].pk,),
    },
    'delete_sequence': {
        'permissions': ('configuration',),
        'methods': ('GET', 'POST'),
        'args': lambda data: (data['sequence'].pk,),
    },
    'create_user': {
        'permissions': ('manage_user',),
        'methods': ('GET', 'POST'),
        'args': None,
    },
    'update_user': {
        'permissions': ('manage_user',),
        'methods': ('GET', 'POST'),
        'args': lambda data: (data['user'].pk,),
    },
    'delete_user': {
        'permissions': ('manage_user',),
        'methods': ('GET', 'POST'),
        'args': lambda data: (data['user'].pk,),
    },
}


@pytest.fixture(params=PERMISSIONS)
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

    user = factories.UserFactory.create(
        username='user_a',
        institution=johns_hopkins,
    )

    phantom = factories.PhantomFactory(institution=johns_hopkins)
    machine = factories.MachineFactory(institution=johns_hopkins)
    sequence = factories.SequenceFactory(institution=johns_hopkins)

    return {
        'permission': f'common.{request.param}',
        'current_user': current_user,
        'user': user,
        'phantom': phantom,
        'machine': machine,
        'sequence': sequence,
    }


@pytest.mark.parametrize('url_name', VIEW_PERMISSIONS.keys())
def test_permissions(permissions_data, url_name):
    user = permissions_data['user']
    permissions = VIEW_PERMISSIONS[url_name]['permissions']
    methods = VIEW_PERMISSIONS[url_name]['methods']
    args = VIEW_PERMISSIONS[url_name]['args']
    url = reverse(url_name, args=args(permissions_data) if args else None)

    client = Client()
    client.force_login(user)

    if all(user.has_perm(permission) for permission in permissions):
        for method in methods:
            assert getattr(client, method.lower())(url).status_code in (200, 302)
    else:
        for method in methods:
            assert getattr(client, method.lower())(url).status_code == 403


@pytest.mark.django_db
def test_institution_permissions():

    # populate database
    configuration_permission = Permission.objects.get(codename='configuration')

    medical_physicists = factories.GroupFactory.create(name='Medical Physicist')
    medical_physicists.permissions.add(configuration_permission)

    johns_hopkins = factories.InstitutionFactory.create(name='Johns Hopkins')
    utexas = factories.InstitutionFactory.create(name='University of Texas')

    user_a = factories.UserFactory.create(
        username="user_a",
        institution=johns_hopkins,
        groups=[medical_physicists],
    )

    user_b = factories.UserFactory.create(
        username="user_b",
        institution=utexas,
        groups=[medical_physicists],
    )

    phantom = factories.PhantomFactory(institution=johns_hopkins)
    machine = factories.MachineFactory(institution=johns_hopkins)
    sequence = factories.SequenceFactory(institution=johns_hopkins)

    assert_can_view(user_a, (
        reverse('update_phantom', args=(phantom.pk,)),
        reverse('delete_phantom', args=(phantom.pk,)),
        reverse('update_machine', args=(machine.pk,)),
        reverse('delete_machine', args=(machine.pk,)),
        reverse('update_sequence', args=(sequence.pk,)),
        reverse('delete_sequence', args=(sequence.pk,)),
    ))

    assert_cannot_view(user_b, (
        reverse('update_phantom', args=(phantom.pk,)),
        reverse('delete_phantom', args=(phantom.pk,)),
        reverse('update_machine', args=(machine.pk,)),
        reverse('delete_machine', args=(machine.pk,)),
        reverse('update_sequence', args=(sequence.pk,)),
        reverse('delete_sequence', args=(sequence.pk,)),
    ))

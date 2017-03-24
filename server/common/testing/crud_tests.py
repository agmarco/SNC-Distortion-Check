import pytest

from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import Permission

from server.common import factories
from server.common.models import Phantom, Machine, Sequence, GoldenFiducials
from .utils import validate_create_view, validate_update_view, validate_delete_view, assert_cannot_post


@pytest.mark.django_db
def test_phantoms():

    # populate database
    configuration_permission = Permission.objects.get(codename='configuration')

    medical_physicists = factories.GroupFactory.create(name='Medical Physicist')
    medical_physicists.permissions.add(configuration_permission)

    johns_hopkins = factories.InstitutionFactory.create(name='Johns Hopkins')

    user = factories.UserFactory.create(
        username="medical_physicist",
        institution=johns_hopkins,
        groups=[medical_physicists],
    )

    fiducials_a = factories.FiducialsFactory()

    phantom_model = factories.PhantomModelFactory(
        name='CIRS 603A',
        model_number='603A',
        cad_fiducials=fiducials_a,
    )

    client = Client()
    client.force_login(user)

    create_phantom_data = {
        'name': 'Create Phantom',
        'model': str(phantom_model.pk),
        'serial_number': '12345',
    }
    update_phantom_data = {'name': 'Update Phantom'}

    phantom = validate_create_view(user, reverse('create_phantom'), Phantom, create_phantom_data)

    # check that a GoldenFiducials was created and activated
    assert phantom.goldenfiducials_set.count() == 1
    assert phantom.goldenfiducials_set.first().is_active
    assert phantom.active_golden_fiducials.fiducials == phantom.model.cad_fiducials

    # test deletion of an inactive GoldenFiducials
    golden_fiducials = factories.GoldenFiducialsFactory(phantom=phantom, type=GoldenFiducials.RAW)
    validate_delete_view(user, reverse('delete_golden_fiducials', args=(phantom.pk, golden_fiducials.pk)), GoldenFiducials)

    # test deletion of an active GoldenFiducials, and the CAD GoldenFiducials when inactive
    golden_fiducials = factories.GoldenFiducialsFactory(phantom=phantom, type=GoldenFiducials.RAW)
    golden_fiducials.activate()

    assert_cannot_post(user, (reverse('delete_golden_fiducials', args=(phantom.pk, golden_fiducials.pk)),))
    assert_cannot_post(user, (reverse('delete_golden_fiducials', args=(phantom.pk, phantom.active_golden_fiducials.pk)),))

    validate_update_view(user, reverse('update_phantom', args=(phantom.pk,)), Phantom, update_phantom_data)
    validate_delete_view(user, reverse('delete_phantom', args=(phantom.pk,)), Phantom)

    create_machine_data = {
        'name': 'Create Machine',
        'model': 'Create Model',
        'manufacturer': 'Create Manufacturer',
    }
    update_machine_data = {
        'name': 'Update Machine',
        'model': 'Update Model',
        'manufacturer': 'Update Manufacturer',
    }

    machine = validate_create_view(user, reverse('create_machine'), Machine, create_machine_data)
    validate_update_view(user, reverse('update_machine', args=(machine.pk,)), Machine, update_machine_data)
    validate_delete_view(user, reverse('delete_machine', args=(machine.pk,)), Machine)

    create_sequence_data = {
        'name': 'Create Sequence',
        'instructions': 'Create Instructions',
    }
    update_sequence_data = {
        'name': 'Update Sequence',
        'instructions': 'Update Instructions',
    }

    sequence = validate_create_view(user, reverse('create_sequence'), Sequence, create_sequence_data)
    validate_update_view(user, reverse('update_sequence', args=(sequence.pk,)), Sequence, update_sequence_data)
    validate_delete_view(user, reverse('delete_sequence', args=(sequence.pk,)), Sequence)


@pytest.mark.django_db
def test_machines():

    # populate database
    configuration_permission = Permission.objects.get(codename='configuration')

    medical_physicists = factories.GroupFactory.create(name='Medical Physicist')
    medical_physicists.permissions.add(configuration_permission)

    johns_hopkins = factories.InstitutionFactory.create(name='Johns Hopkins')

    user = factories.UserFactory.create(
        username="medical_physicist",
        institution=johns_hopkins,
        groups=[medical_physicists],
    )

    client = Client()
    client.force_login(user)

    create_machine_data = {
        'name': 'Create Machine',
        'model': 'Create Model',
        'manufacturer': 'Create Manufacturer',
    }
    update_machine_data = {
        'name': 'Update Machine',
        'model': 'Update Model',
        'manufacturer': 'Update Manufacturer',
    }

    machine = validate_create_view(user, reverse('create_machine'), Machine, create_machine_data)
    validate_update_view(user, reverse('update_machine', args=(machine.pk,)), Machine, update_machine_data)
    validate_delete_view(user, reverse('delete_machine', args=(machine.pk,)), Machine)


@pytest.mark.django_db
def test_sequences():

    # populate database
    configuration_permission = Permission.objects.get(codename='configuration')

    medical_physicists = factories.GroupFactory.create(name='Medical Physicist')
    medical_physicists.permissions.add(configuration_permission)

    johns_hopkins = factories.InstitutionFactory.create(name='Johns Hopkins')

    user = factories.UserFactory.create(
        username="medical_physicist",
        institution=johns_hopkins,
        groups=[medical_physicists],
    )

    client = Client()
    client.force_login(user)

    create_sequence_data = {
        'name': 'Create Sequence',
        'instructions': 'Create Instructions',
    }
    update_sequence_data = {
        'name': 'Update Sequence',
        'instructions': 'Update Instructions',
    }

    sequence = validate_create_view(user, reverse('create_sequence'), Sequence, create_sequence_data)
    validate_update_view(user, reverse('update_sequence', args=(sequence.pk,)), Sequence, update_sequence_data)
    validate_delete_view(user, reverse('delete_sequence', args=(sequence.pk,)), Sequence)

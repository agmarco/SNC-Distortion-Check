import pytest

from django.test import Client
from django.urls import reverse
from django.db import models
from django.contrib.auth.models import Permission

from server.common import factories
from server.common.models import Phantom, Machine, Sequence, GoldenFiducials


def _validate_fields(model, data):
    for field_name in data.keys():

        # if the field is a foreign key, check that the primary key equals the POST data
        if isinstance(model._meta.get_field(field_name), models.ForeignKey):
            assert getattr(model, field_name).pk == int(data[field_name])
        else:
            assert getattr(model, field_name) == data[field_name]


def _test_create_view(user, url, model_class, data):
    current_count = model_class.objects.count()

    client = Client()
    client.force_login(user)
    client.post(url, data=data)

    assert model_class.objects.count() == current_count + 1
    model = model_class.objects.all().order_by('-last_modified_on').first()
    _validate_fields(model, data)
    assert model.institution == user.institution

    return model


def _test_update_view(user, url, model_class, data):
    current_count = model_class.objects.count()

    client = Client()
    client.force_login(user)
    client.post(url, data=data)

    assert model_class.objects.count() == current_count
    model = model_class.objects.all().order_by('-last_modified_on').first()
    _validate_fields(model, data)

    return model


def _test_delete_view(user, url, model_class):
    current_count = model_class.objects.count()

    client = Client()
    client.force_login(user)
    client.post(url)

    assert model_class.objects.count() == current_count
    model = model_class.objects.all().order_by('-last_modified_on').first()
    assert model.deleted

    return model


@pytest.mark.django_db
def test_crud():

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

    phantom = _test_create_view(user, reverse('create_phantom'), Phantom, create_phantom_data)

    # check that a GoldenFiducials was created and activated
    assert phantom.goldenfiducials_set.count() == 1

    # test deletion of an inactive GoldenFiducials
    fiducials_b = factories.FiducialsFactory()
    golden_fiducials = factories.GoldenFiducialsFactory(
        phantom=phantom,
        fiducials=fiducials_b,
        type=GoldenFiducials.RAW,
        is_active=False,
    )
    _test_delete_view(user, reverse('delete_golden_fiducials', args=(phantom.pk, golden_fiducials.pk)), GoldenFiducials)

    _test_update_view(user, reverse('update_phantom', args=(phantom.pk,)), Phantom, update_phantom_data)
    _test_delete_view(user, reverse('delete_phantom', args=(phantom.pk,)), Phantom)

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

    machine = _test_create_view(user, reverse('create_machine'), Machine, create_machine_data)
    _test_update_view(user, reverse('update_machine', args=(machine.pk,)), Machine, update_machine_data)
    _test_delete_view(user, reverse('delete_machine', args=(machine.pk,)), Machine)

    create_sequence_data = {
        'name': 'Create Sequence',
        'instructions': 'Create Instructions',
    }
    update_sequence_data = {
        'name': 'Update Sequence',
        'instructions': 'Update Instructions',
    }

    sequence = _test_create_view(user, reverse('create_sequence'), Sequence, create_sequence_data)
    _test_update_view(user, reverse('update_sequence', args=(sequence.pk,)), Sequence, update_sequence_data)
    _test_delete_view(user, reverse('delete_sequence', args=(sequence.pk,)), Sequence)

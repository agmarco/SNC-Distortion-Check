import pytest

from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import Permission

from server.common import factories
from server.common.models import Phantom, Machine, Sequence


def _test_create_view(user, url, model_class, data):
    client = Client()
    client.force_login(user)
    client.post(url, data=data)

    assert model_class.objects.count() == 1
    model = model_class.objects.first()

    for key in data.keys():
        assert getattr(model, key) == data[key]
    assert model.institution == user.institution

    return model


def _test_update_view(user, url, model_class, data):
    client = Client()
    client.force_login(user)
    client.post(url, data=data)

    assert model_class.objects.count() == 1
    model = model_class.objects.first()

    for key in data.keys():
        assert getattr(model, key) == data[key]

    return model


def _test_delete_view(user, url, model_class):
    client = Client()
    client.force_login(user)
    client.post(url)

    assert model_class.objects.count() == 1
    model = model_class.objects.first()
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

    phantom_model = factories.PhantomModelFactory(
        name='CIRS 603A',
        model_number='603A',
    )

    client = Client()
    client.force_login(user)

    phantom = _test_create_view(user, reverse('create_phantom'), Phantom, {
        'name': 'Create Phantom',
        'model': phantom_model,
        'serial_number': '12345',
    })

    # reverse and reverse_lazy both cause circular imports when called with an argument
    _test_update_view(user, f'/phantoms/edit/{phantom.pk}/', Phantom, {'name': 'Update Phantom'})

    _test_delete_view(user, f'/phantoms/delete/{phantom.pk}/', Phantom)

    machine = _test_create_view(user, reverse('create_machine'), Machine, {
        'name': 'Create Machine',
        'model': 'Creatre Model',
        'manufacturer': 'Create Manufacturer',
    })

    _test_update_view(user, f'/machines/edit/{machine.pk}/', Machine, {
        'name': 'Update Machine',
        'model': 'Update Model',
        'manufacturer': 'Update Manufacturer',
    })

    _test_delete_view(user, f'/machines/delete/{machine.pk}/', Machine)

    sequence = _test_create_view(user, reverse('create_sequence'), Sequence, {
        'name': 'Create Sequence',
        'instructions': 'Create Instructions',
    })

    _test_update_view(user, f'/sequences/edit/{sequence.pk}/', Sequence, {
        'name': 'Update Sequence',
        'instructions': 'Update Instructions',
    })

    _test_delete_view(user, f'/sequences/delete/{sequence.pk}/', Sequence)

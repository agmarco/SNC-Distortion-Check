import pytest

from django.test import Client
from django.urls import reverse_lazy
from django.contrib.auth.models import Permission

from server.common import factories
from server.common.models import Phantom


@pytest.mark.django_db
def test_phantom_crud():

    # populate database
    configuration_permission = Permission.objects.get(codename='configuration')

    medical_physicists = factories.GroupFactory.create(name='Medical Physicist')
    medical_physicists.permissions.add(configuration_permission)

    john_hopkins = factories.InstitutionFactory.create(name='John Hopkins')

    user = factories.UserFactory.create(
        username="medical_physicist",
        institution=john_hopkins,
        groups=[medical_physicists],
    )

    client = Client()
    client.force_login(user)

    # add phantom
    url = reverse_lazy('add_phantom')

    phantom_name = 'Add Phantom'
    phantom_model = Phantom.CIRS_603A
    phantom_serial_number = '12345'

    client.post(url, data={
        'name': phantom_name,
        'model': phantom_model,
        'serial_number': phantom_serial_number,
    })

    assert Phantom.objects.count() == 1
    phantom = Phantom.objects.first()
    assert phantom.name == phantom_name
    assert phantom.model == phantom_model
    assert phantom.serial_number == phantom_serial_number
    assert phantom.institution == user.institution

    # edit phantom
    url = reverse_lazy('edit_phantom', phantom.pk)
    phantom_name = 'Edit Phantom'

    client.post(url, data={'name': phantom_name})

    assert Phantom.objects.count() == 1
    phantom = Phantom.objects.first()
    assert phantom.name == phantom_name

    # delete phantom

    url = reverse_lazy('delete_phantom', phantom.pk)

    client.post(url)

    assert Phantom.objects.count() == 1
    phantom = Phantom.objects.first()
    assert phantom.deleted

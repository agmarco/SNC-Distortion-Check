import pytest

from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import Permission

from server.common import factories
from server.common.models import Phantom, Machine, Sequence


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
    url = reverse('add_phantom')
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
    url = f'/phantoms/edit/{phantom.pk}/'  # reverse and reverse_lazy both cause circular imports when called with an argument
    phantom_name = 'Edit Phantom'

    client.post(url, data={'name': phantom_name})

    assert Phantom.objects.count() == 1
    phantom = Phantom.objects.first()
    assert phantom.name == phantom_name

    # delete phantom

    url = f'/phantoms/delete/{phantom.pk}/'

    client.post(url)

    assert Phantom.objects.count() == 1
    phantom = Phantom.objects.first()
    assert phantom.deleted


@pytest.mark.django_db
def test_machine_crud():

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

    # add machine
    url = reverse('add_machine')
    machine_name = 'Add Machine'
    machine_model = 'Add Model'
    machine_manufacturer = 'Add Manufacturer'

    client.post(url, data={
        'name': machine_name,
        'model': machine_model,
        'manufacturer': machine_manufacturer,
    })

    assert Machine.objects.count() == 1
    machine = Machine.objects.first()
    assert machine.name == machine_name
    assert machine.model == machine_model
    assert machine.manufacturer == machine_manufacturer
    assert machine.institution == user.institution

    # edit machine
    url = f'/machines/edit/{machine.pk}/'
    machine_name = 'Edit Machine'
    machine_model = 'Edit Model'
    machine_manufacturer = 'Edit Manufacturer'

    client.post(url, data={
        'name': machine_name,
        'model': machine_model,
        'manufacturer': machine_manufacturer,
    })

    assert Machine.objects.count() == 1
    machine = Machine.objects.first()
    assert machine.name == machine_name
    assert machine.model == machine_model
    assert machine.manufacturer == machine_manufacturer

    # delete machine

    url = f'/machines/delete/{machine.pk}/'

    client.post(url)

    assert Machine.objects.count() == 1
    machine = Machine.objects.first()
    assert machine.deleted


@pytest.mark.django_db
def test_sequence_crud():

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

    # add sequence
    url = reverse('add_sequence')
    sequence_name = 'Add Sequence'
    sequence_instructions = 'Add Instructions'

    client.post(url, data={
        'name': sequence_name,
        'instructions': sequence_instructions,
    })

    assert Sequence.objects.count() == 1
    sequence = Sequence.objects.first()
    assert sequence.name == sequence_name
    assert sequence.instructions == sequence_instructions
    assert sequence.institution == user.institution

    # edit sequence
    url = f'/sequences/edit/{sequence.pk}/'
    sequence_name = 'Edit Sequence'
    sequence_instructions = 'Edit Instructions'

    client.post(url, data={
        'name': sequence_name,
        'instructions': sequence_instructions,
    })

    assert Sequence.objects.count() == 1
    sequence = Sequence.objects.first()
    assert sequence.name == sequence_name
    assert sequence.instructions == sequence_instructions

    # delete sequence

    url = f'/sequences/delete/{sequence.pk}/'

    client.post(url)

    assert Sequence.objects.count() == 1
    sequence = Sequence.objects.first()
    assert sequence.deleted

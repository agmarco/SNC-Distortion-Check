import pytest
from django.contrib.auth.models import Permission

from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from server.common.factories import UserFactory, GroupFactory, InstitutionFactory, PhantomFactory, SequenceFactory, MachineFactory
from server.common.models import Phantom


@pytest.mark.django_db
def test_configuration_permissions():

    # populate database
    configuration_permission = Permission.objects.get(codename='configuration')

    medical_physicists = GroupFactory.create(name='medical_physicists')
    medical_physicists.permissions.add(configuration_permission)
    therapists = GroupFactory.create(name='therapists')

    john_hopkins = InstitutionFactory.create(name='John Hopkins')

    medical_physicist = UserFactory.create(
        username="medical_physicist",
        first_name="Mary",
        last_name="Jane",
        email="mary.jane@johnhopkins.edu",
        institution=john_hopkins,
        groups=[medical_physicists],
    )

    therapist = UserFactory.create(
        username="therapist",
        first_name="John",
        last_name="Doe",
        email="john.doe@johnhopkins.edu",
        institution=john_hopkins,
        groups=[therapists],
    )

    client = Client()
    url = reverse('configuration')

    # non-medical-physicist user unauthorized
    client.force_login(therapist)
    response = client.get(url)
    assert response.status_code == 403

    # medical-physicist user authorized
    client.force_login(medical_physicist)
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_configuration_context():

    # populate database
    configuration_permission = Permission.objects.get(codename='configuration')

    medical_physicists = GroupFactory.create(name='medical_physicists')
    medical_physicists.permissions.add(configuration_permission)

    john_hopkins = InstitutionFactory.create(name='John Hopkins')
    utexas = InstitutionFactory.create(name='University of Texas')

    user_a = UserFactory.create(
        username="user_a",
        first_name="Mary",
        last_name="Jane",
        email="mary.jane@johnhopkins.edu",
        institution=john_hopkins,
        groups=[medical_physicists],
    )
    user_b = UserFactory.create(
        username="user_b",
        first_name="John",
        last_name="Doe",
        email="john.doe@johnhopkins.edu",
        institution=john_hopkins,
        groups=[medical_physicists],
        deleted=True,
    )
    user_c = UserFactory.create(
        username="user_c",
        first_name="Gustav",
        last_name="Mahler",
        email="gustav.mahler@utexas.edu",
        institution=utexas,
        groups=[medical_physicists],
    )

    machine_a = MachineFactory.create(
        name='MRI Scanner East',
        institution=john_hopkins,
    )
    machine_b = MachineFactory.create(
        name='MRI Scanner West',
        institution=john_hopkins,
        deleted=True,
    )
    machine_c = MachineFactory.create(
        name='MRI Scanner North',
        institution=utexas,
    )

    phantom_a = PhantomFactory(
        name='Head Phantom 1',
        model=Phantom.CIRS_603A,
        institution=john_hopkins,
    )
    phantom_b = PhantomFactory(
        name='Head Phantom 2',
        model=Phantom.CIRS_603A,
        institution=john_hopkins,
        deleted=True,
    )
    phantom_c = PhantomFactory(
        name='Body Phantom',
        model=Phantom.CIRS_604,
        institution=utexas,
    )

    sequence_a = SequenceFactory(
        name="T1-Weighted Abdominal",
        institution=john_hopkins,
    )
    sequence_b = SequenceFactory(
        name="T1-Weighted Neural",
        institution=john_hopkins,
        deleted=True,
    )
    sequence_c = SequenceFactory(
        name="T2-Weighted Neural",
        institution=utexas,
    )

    client = Client()
    url = reverse('configuration')

    client.force_login(user_a)
    response = client.get(url)

    print(response)

    phantoms = response.context['phantoms']
    machines = response.context['machines']
    sequences = response.context['sequences']
    users = response.context['users']

    # only display items from the user's institution
    assert all([phantom.institution.pk == user_a.institution.pk for phantom in phantoms])
    assert all([machine.institution.pk == user_a.institution.pk for machine in machines])
    assert all([sequence.institution.pk == user_a.institution.pk for sequence in sequences])
    assert all([user.institution.pk == user_a.institution.pk for user in users])

    # don't display deleted items
    assert all([not phantom.deleted for phantom in phantoms])
    assert all([not machine.deleted for machine in machines])
    assert all([not sequence.deleted for sequence in sequences])
    assert all([not user.deleted for user in users])

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

    medical_physicists = GroupFactory.create(name='Medical Physicist')
    medical_physicists.permissions.add(configuration_permission)
    therapists = GroupFactory.create(name='Therapist')

    john_hopkins = InstitutionFactory.create(name='John Hopkins')

    medical_physicist = UserFactory.create(
        username="medical_physicist",
        institution=john_hopkins,
        groups=[medical_physicists],
    )
    therapist = UserFactory.create(
        username="therapist",
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

    medical_physicists = GroupFactory.create(name='Medical Physicist')
    medical_physicists.permissions.add(configuration_permission)

    john_hopkins = InstitutionFactory.create(name='John Hopkins')
    utexas = InstitutionFactory.create(name='University of Texas')

    user_a = UserFactory.create(
        username="user_a",
        institution=john_hopkins,
        groups=[medical_physicists],
    )
    user_b = UserFactory.create(
        username="user_b",
        institution=john_hopkins,
        groups=[medical_physicists],
        deleted=True,
    )
    user_c = UserFactory.create(
        username="user_c",
        institution=utexas,
        groups=[medical_physicists],
    )

    machine_a = MachineFactory.create(institution=john_hopkins)
    machine_b = MachineFactory.create(institution=john_hopkins, deleted=True)
    machine_c = MachineFactory.create(institution=utexas)

    phantom_a = PhantomFactory(institution=john_hopkins)
    phantom_b = PhantomFactory(institution=john_hopkins, deleted=True)
    phantom_c = PhantomFactory(institution=utexas)

    sequence_a = SequenceFactory(institution=john_hopkins)
    sequence_b = SequenceFactory(institution=john_hopkins, deleted=True)
    sequence_c = SequenceFactory(institution=utexas)

    client = Client()
    url = reverse('configuration')

    client.force_login(user_a)
    response = client.get(url)

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

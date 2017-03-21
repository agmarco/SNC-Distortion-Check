import pytest

from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import Permission

from server.common import factories


def _assert_can_view(user, urls):
    client = Client()
    client.force_login(user)

    for url in urls:
        response = client.get(url)
        assert response.status_code == 200


def _assert_cannot_view(user, urls):
    client = Client()
    client.force_login(user)

    for url in urls:
        response = client.get(url)
        assert response.status_code == 403


@pytest.mark.django_db
def test_medical_phycisist_permissions():

    # populate database
    configuration_permission = Permission.objects.get(codename='configuration')

    medical_physicists = factories.GroupFactory.create(name='Medical Physicist')
    medical_physicists.permissions.add(configuration_permission)

    john_hopkins = factories.InstitutionFactory.create(name='John Hopkins')

    medical_physicist = factories.UserFactory.create(
        username="medical_physicist",
        institution=john_hopkins,
        groups=[medical_physicists],
    )

    phantom = factories.PhantomFactory(institution=john_hopkins)
    machine = factories.MachineFactory(institution=john_hopkins)
    sequence = factories.SequenceFactory(institution=john_hopkins)

    _assert_can_view(medical_physicist, (
        reverse('configuration'),
        reverse('add_phantom'),
        f'/phantoms/edit/{phantom.pk}/',
        f'/phantoms/delete/{phantom.pk}/',
        reverse('add_machine'),
        f'/machines/edit/{machine.pk}/',
        f'/machines/delete/{machine.pk}',
        reverse('add_sequence'),
        f'/sequences/edit/{sequence.pk}/',
        f'/sequences/delete/{sequence.pk}/',
    ))


@pytest.mark.django_db
def test_medical_phycisist_permissions():

    # populate database
    therapists = factories.GroupFactory.create(name='Therapist')

    john_hopkins = factories.InstitutionFactory.create(name='John Hopkins')

    therapist = factories.UserFactory.create(
        username="therapist",
        institution=john_hopkins,
        groups=[therapists],
    )

    phantom = factories.PhantomFactory(institution=john_hopkins)
    machine = factories.MachineFactory(institution=john_hopkins)
    sequence = factories.SequenceFactory(institution=john_hopkins)

    _assert_cannot_view(therapist, (
        reverse('configuration'),
        reverse('add_phantom'),
        f'/phantoms/edit/{phantom.pk}/',
        f'/phantoms/delete/{phantom.pk}/',
        reverse('add_machine'),
        f'/machines/edit/{machine.pk}/',
        f'/machines/delete/{machine.pk}/',
        reverse('add_sequence'),
        f'/sequences/edit/{sequence.pk}/',
        f'/sequences/delete/{sequence.pk}/',
    ))


@pytest.mark.django_db
def test_institution_permissions():

    # populate database
    configuration_permission = Permission.objects.get(codename='configuration')

    medical_physicists = factories.GroupFactory.create(name='Medical Physicist')
    medical_physicists.permissions.add(configuration_permission)

    john_hopkins = factories.InstitutionFactory.create(name='John Hopkins')
    utexas = factories.InstitutionFactory.create(name='University of Texas')

    user_a = factories.UserFactory.create(
        username="user_a",
        institution=john_hopkins,
        groups=[medical_physicists],
    )

    user_b = factories.UserFactory.create(
        username="user_b",
        institution=utexas,
        groups=[medical_physicists],
    )

    phantom = factories.PhantomFactory(institution=john_hopkins)
    machine = factories.MachineFactory(institution=john_hopkins)
    sequence = factories.SequenceFactory(institution=john_hopkins)

    _assert_can_view(user_a, (
        f'/phantoms/edit/{phantom.pk}/',
        f'/phantoms/delete/{phantom.pk}/',
        f'/machines/edit/{machine.pk}/',
        f'/machines/delete/{machine.pk}/',
        f'/sequences/edit/{sequence.pk}/',
        f'/sequences/delete/{sequence.pk}/',
    ))

    _assert_cannot_view(user_b, (
        f'/phantoms/edit/{phantom.pk}/',
        f'/phantoms/delete/{phantom.pk}/',
        f'/machines/edit/{machine.pk}/',
        f'/machines/delete/{machine.pk}/',
        f'/sequences/edit/{sequence.pk}/',
        f'/sequences/delete/{sequence.pk}/',
    ))

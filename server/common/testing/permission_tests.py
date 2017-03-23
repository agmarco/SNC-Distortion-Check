import pytest

from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import Permission

from server.common import factories


def _assert_can_view(user, urls):
    client = Client()
    client.force_login(user)

    for url in urls:
        assert client.get(url).status_code in (200, 302, 405)
        assert client.post(url).status_code in (200, 302, 405)
        assert client.put(url).status_code in (200, 302, 405)
        assert client.patch(url).status_code in (200, 302, 405)
        assert client.delete(url).status_code in (200, 302, 405)


def _assert_cannot_view(user, urls):
    client = Client()
    client.force_login(user)

    for url in urls:
        assert client.get(url).status_code in (403, 405)
        assert client.post(url).status_code in (403, 405)
        assert client.put(url).status_code in (403, 405)
        assert client.patch(url).status_code in (403, 405)
        assert client.delete(url).status_code in (403, 405)


@pytest.mark.django_db
def test_medical_phycisist_permissions():

    # populate database
    configuration_permission = Permission.objects.get(codename='configuration')

    medical_physicists = factories.GroupFactory.create(name='Medical Physicist')
    medical_physicists.permissions.add(configuration_permission)

    johns_hopkins = factories.InstitutionFactory.create(name='Johns Hopkins')

    medical_physicist = factories.UserFactory.create(
        username="medical_physicist",
        institution=johns_hopkins,
        groups=[medical_physicists],
    )

    phantom = factories.PhantomFactory(institution=johns_hopkins)
    machine = factories.MachineFactory(institution=johns_hopkins)
    sequence = factories.SequenceFactory(institution=johns_hopkins)

    _assert_can_view(medical_physicist, (
        reverse('configuration'),
        reverse('create_phantom'),
        reverse('update_phantom', args=(phantom.pk,)),
        reverse('delete_phantom', args=(phantom.pk,)),
        reverse('create_machine'),
        reverse('update_machine', args=(machine.pk,)),
        reverse('delete_machine', args=(machine.pk,)),
        reverse('create_sequence'),
        reverse('update_sequence', args=(sequence.pk,)),
        reverse('delete_sequence', args=(sequence.pk,)),
    ))


@pytest.mark.django_db
def test_therapist_permissions():

    # populate database
    therapists = factories.GroupFactory.create(name='Therapist')

    johns_hopkins = factories.InstitutionFactory.create(name='Johns Hopkins')

    therapist = factories.UserFactory.create(
        username="therapist",
        institution=johns_hopkins,
        groups=[therapists],
    )

    phantom = factories.PhantomFactory(institution=johns_hopkins)
    machine = factories.MachineFactory(institution=johns_hopkins)
    sequence = factories.SequenceFactory(institution=johns_hopkins)

    _assert_cannot_view(therapist, (
        reverse('configuration'),
        reverse('create_phantom'),
        reverse('update_phantom', args=(phantom.pk,)),
        reverse('delete_phantom', args=(phantom.pk,)),
        reverse('create_machine'),
        reverse('update_machine', args=(machine.pk,)),
        reverse('delete_machine', args=(machine.pk,)),
        reverse('create_sequence'),
        reverse('update_sequence', args=(sequence.pk,)),
        reverse('delete_sequence', args=(sequence.pk,)),
    ))


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

    _assert_can_view(user_a, (
        reverse('update_phantom', args=(phantom.pk,)),
        reverse('delete_phantom', args=(phantom.pk,)),
        reverse('update_machine', args=(machine.pk,)),
        reverse('delete_machine', args=(machine.pk,)),
        reverse('update_sequence', args=(sequence.pk,)),
        reverse('delete_sequence', args=(sequence.pk,)),
    ))

    _assert_cannot_view(user_b, (
        reverse('update_phantom', args=(phantom.pk,)),
        reverse('delete_phantom', args=(phantom.pk,)),
        reverse('update_machine', args=(machine.pk,)),
        reverse('delete_machine', args=(machine.pk,)),
        reverse('update_sequence', args=(sequence.pk,)),
        reverse('delete_sequence', args=(sequence.pk,)),
    ))

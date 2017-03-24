import pytest

from django.urls import reverse
from django.contrib.auth.models import Permission

from server.common import factories
from .utils import assert_can_view, assert_cannot_view


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

    assert_can_view(medical_physicist, (
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

    assert_cannot_view(therapist, (
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

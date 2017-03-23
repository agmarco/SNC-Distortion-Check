import pytest


from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import Permission

from server.common import factories


@pytest.mark.django_db
def test_configuration_context():

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
        institution=johns_hopkins,
        groups=[medical_physicists],
        deleted=True,
    )
    user_c = factories.UserFactory.create(
        username="user_c",
        institution=utexas,
        groups=[medical_physicists],
    )

    machine_a = factories.MachineFactory.create(institution=johns_hopkins)
    machine_b = factories.MachineFactory.create(institution=johns_hopkins, deleted=True)
    machine_c = factories.MachineFactory.create(institution=utexas)

    phantom_a = factories.PhantomFactory(institution=johns_hopkins)
    phantom_b = factories.PhantomFactory(institution=johns_hopkins, deleted=True)
    phantom_c = factories.PhantomFactory(institution=utexas)

    sequence_a = factories.SequenceFactory(institution=johns_hopkins)
    sequence_b = factories.SequenceFactory(institution=johns_hopkins, deleted=True)
    sequence_c = factories.SequenceFactory(institution=utexas)

    client = Client()
    url = reverse('configuration')

    client.force_login(user_a)
    response = client.get(url)

    phantoms = response.context['phantoms']
    machines = response.context['machines']
    sequences = response.context['sequences']
    users = response.context['users']

    # only display items from the user's institution
    assert all(phantom.institution == user_a.institution for phantom in phantoms)
    assert all(machine.institution == user_a.institution for machine in machines)
    assert all(sequence.institution == user_a.institution for sequence in sequences)
    assert all(user.institution == user_a.institution for user in users)

    # don't display deleted items
    assert all(not phantom.deleted for phantom in phantoms)
    assert all(not machine.deleted for machine in machines)
    assert all(not sequence.deleted for sequence in sequences)
    assert all(not user.deleted for user in users)

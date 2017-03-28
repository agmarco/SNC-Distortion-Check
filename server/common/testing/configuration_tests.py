import pytest

from django.urls import reverse
from django.contrib.auth.models import Permission

from .. import factories


@pytest.mark.django_db
def test_configuration_context(client):
    johns_hopkins = factories.InstitutionFactory.create(name='Johns Hopkins')
    utexas = factories.InstitutionFactory.create(name='University of Texas')
    managers = factories.GroupFactory.create(name="Manager", permissions=Permission.objects.all())
    medical_physicists = factories.GroupFactory.create(name="Medical Physicist", permissions=[Permission.objects.get(codename='configuration')])
    manager = factories.UserFactory.create(username="manager", institution=johns_hopkins, groups=[managers])
    medical_physicist = factories.UserFactory.create(username="medical_physicist", institution=johns_hopkins, groups=[medical_physicists])

    factories.PhantomFactory(institution=johns_hopkins)
    factories.PhantomFactory(institution=johns_hopkins, deleted=True)
    factories.PhantomFactory(institution=utexas)

    factories.MachineFactory.create(institution=johns_hopkins)
    factories.MachineFactory.create(institution=johns_hopkins, deleted=True)
    factories.MachineFactory.create(institution=utexas)

    factories.SequenceFactory(institution=johns_hopkins)
    factories.SequenceFactory(institution=johns_hopkins, deleted=True)
    factories.SequenceFactory(institution=utexas)

    factories.UserFactory.create(username="user_a", institution=johns_hopkins)
    factories.UserFactory.create(username="user_b", institution=johns_hopkins, deleted=True)
    factories.UserFactory.create(username="user_c", institution=utexas)

    url = reverse('configuration')

    client.force_login(manager)
    response = client.get(url)

    phantoms = response.context['phantoms']
    machines = response.context['machines']
    sequences = response.context['sequences']
    users = response.context['users']

    # only display items from the user's institution
    assert all(phantom.institution == manager.institution for phantom in phantoms)
    assert all(machine.institution == manager.institution for machine in machines)
    assert all(sequence.institution == manager.institution for sequence in sequences)
    assert all(user.institution == manager.institution for user in users)

    # don't display deleted items
    assert all(not phantom.deleted for phantom in phantoms)
    assert all(not machine.deleted for machine in machines)
    assert all(not sequence.deleted for sequence in sequences)
    assert all(not user.deleted for user in users)

    # check that a medical physicist can't view users
    client.force_login(medical_physicist)
    response = client.get(url)

    assert 'users' not in response.context

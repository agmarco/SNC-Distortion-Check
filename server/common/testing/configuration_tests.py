import pytest


from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import Permission

from .. import factories


@pytest.mark.django_db
def test_configuration_context():
    johns_hopkins = factories.InstitutionFactory.create(name='Johns Hopkins')
    utexas = factories.InstitutionFactory.create(name='University of Texas')
    group = factories.GroupFactory.create(name="Group", permissions=Permission.objects.all())
    current_user = factories.UserFactory.create(username="current_user", institution=johns_hopkins, groups=[group])

    factories.PhantomFactory(institution=johns_hopkins)
    factories.PhantomFactory(institution=johns_hopkins, deleted=True)
    factories.PhantomFactory(institution=utexas)

    factories.MachineFactory.create(institution=johns_hopkins)
    factories.MachineFactory.create(institution=johns_hopkins, deleted=True)
    factories.MachineFactory.create(institution=utexas)

    factories.SequenceFactory(institution=johns_hopkins)
    factories.SequenceFactory(institution=johns_hopkins, deleted=True)
    factories.SequenceFactory(institution=utexas)

    factories.UserFactory.create(username="user_a", institution=johns_hopkins, groups=[group])
    factories.UserFactory.create(username="user_b", institution=johns_hopkins, groups=[group], deleted=True)
    factories.UserFactory.create(username="user_c", institution=utexas, groups=[group])

    client = Client()
    url = reverse('configuration')

    client.force_login(current_user)
    response = client.get(url)

    phantoms = response.context['phantoms']
    machines = response.context['machines']
    sequences = response.context['sequences']
    users = response.context['users']

    # only display items from the user's institution
    assert all(phantom.institution == current_user.institution for phantom in phantoms)
    assert all(machine.institution == current_user.institution for machine in machines)
    assert all(sequence.institution == current_user.institution for sequence in sequences)
    assert all(user.institution == current_user.institution for user in users)

    # don't display deleted items
    assert all(not phantom.deleted for phantom in phantoms)
    assert all(not machine.deleted for machine in machines)
    assert all(not sequence.deleted for sequence in sequences)
    assert all(not user.deleted for user in users)

import pytest
import json

from django.contrib.auth.models import Permission
from django.urls import reverse

from .. import factories


@pytest.mark.django_db
def test_validate_serial(client):
    johns_hopkins = factories.InstitutionFactory.create(name="Johns Hopkins")
    group = factories.GroupFactory.create(name="Group", permissions=Permission.objects.all())
    phantom_model = factories.PhantomModelFactory(name='CIRS 603A', model_number='603A')
    phantom1 = factories.PhantomFactory(model=phantom_model, serial_number='SN1', institution=johns_hopkins)
    phantom2 = factories.PhantomFactory(model=phantom_model, serial_number='SN2')
    current_user = factories.UserFactory.create(email='current_user@johnshopkins.edu',
                                                institution=johns_hopkins,
                                                groups=[group])

    client.force_login(current_user)

    res = client.post(reverse('validate_serial'), {'serial_number': 'wrong'})
    content = json.loads(res.content)
    assert not content['valid']

    res = client.post(reverse('validate_serial'), {'serial_number': phantom1.serial_number})
    content = json.loads(res.content)
    assert not content['valid']

    res = client.post(reverse('validate_serial'), {'serial_number': phantom2.serial_number})
    content = json.loads(res.content)
    assert content['valid'] and content['model_number'] == phantom1.model.model_number


@pytest.mark.django_db
def test_update_tolerance(client):
    johns_hopkins = factories.InstitutionFactory.create(name="Johns Hopkins")
    group = factories.GroupFactory.create(name="Group", permissions=Permission.objects.all())
    current_user = factories.UserFactory.create(email='current_user@johnshopkins.edu',
                                                institution=johns_hopkins,
                                                groups=[group])
    machine = factories.MachineFactory(institution=current_user.institution)
    sequence = factories.SequenceFactory(institution=current_user.institution)
    machine_sequence_pair = factories.MachineSequencePairFactory(machine=machine, sequence=sequence, tolerance=1)

    client.force_login(current_user)

    client.post(reverse('update_tolerance'), {'pk': machine_sequence_pair.pk, 'tolerance': 2})
    machine_sequence_pair.refresh_from_db()
    assert machine_sequence_pair.tolerance == 2

import json

import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse

from ..models import Machine, Sequence, Phantom
from .. import factories


@pytest.mark.django_db
def test_upload_scan_context(client):
    johns_hopkins = factories.InstitutionFactory.create(name="Johns Hopkins")
    utexas = factories.InstitutionFactory.create(name="University of Texas")
    group = factories.GroupFactory.create(name="Group", permissions=Permission.objects.all())
    current_user = factories.UserFactory.create(email='current_user@johnshopkins.edu', institution=johns_hopkins, groups=[group])

    machine_a = factories.MachineFactory.create(
        name='MRI Scanner East',
        institution=johns_hopkins,
    )
    machine_b = factories.MachineFactory.create(
        name='MRI Scanner West',
        institution=utexas,
    )

    sequence_a = factories.SequenceFactory(
        name="T1-Weighted Abdominal",
        institution=johns_hopkins,
    )
    sequence_b = factories.SequenceFactory(
        name="T1-Weighted Neural",
        institution=utexas,
    )

    phantom_model = factories.PhantomModelFactory(name='CIRS 603A', model_number='603A')

    phantom_a = factories.PhantomFactory(
        model=phantom_model,
        serial_number='A123',
        institution=johns_hopkins,
    )
    phantom_b = factories.PhantomFactory(
        model=phantom_model,
        serial_number='B123',
        institution=utexas,
    )

    client.force_login(current_user)

    res = client.get(reverse('upload_scan'))
    machines = json.loads(res.context['machines_json'])
    sequences = json.loads(res.context['sequences_json'])
    phantoms = json.loads(res.context['phantoms_json'])

    for machine_data in machines:
        machine = Machine.objects.get(pk=machine_data['pk'])
        assert machine.institution == current_user.institution

    for sequence_data in sequences:
        sequence = Sequence.objects.get(pk=sequence_data['pk'])
        assert sequence.institution == current_user.institution

    for phantom_data in phantoms:
        phantom = Phantom.objects.get(pk=phantom_data['pk'])
        assert phantom.institution == current_user.institution

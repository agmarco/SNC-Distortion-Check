import pytest
import json

from django.contrib.auth.models import Permission
from django.urls import reverse

from ..models import MachineSequencePair, Scan
from .. import factories


@pytest.mark.django_db
def test_machine_sequences_context(client):
    johns_hopkins = factories.InstitutionFactory.create(name="Johns Hopkins")
    utexas = factories.InstitutionFactory.create(name="University of Texas")
    group = factories.GroupFactory.create(name="Group", permissions=Permission.objects.all())
    current_user = factories.UserFactory.create(username='current_user', institution=johns_hopkins, groups=[group])

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

    factories.MachineSequencePairFactory(
        machine=machine_a,
        sequence=sequence_a,
        tolerance=1.75,
    )
    factories.MachineSequencePairFactory(
        machine=machine_b,
        sequence=sequence_b,
        tolerance=1.75,
    )

    client.force_login(current_user)

    res = client.get(reverse('landing'))
    machine_sequence_pairs = json.loads(res.context['machine_sequence_pairs'])
    for pair_data in machine_sequence_pairs:
        pair = MachineSequencePair.objects.get(pk=pair_data['pk'])
        assert pair.institution == current_user.institution

    res = client.get(reverse('machine_sequences'))
    machine_sequence_pairs = json.loads(res.context['machine_sequence_pairs'])
    for pair_data in machine_sequence_pairs:
        pair = MachineSequencePair.objects.get(pk=pair_data['pk'])
        assert pair.institution == current_user.institution


@pytest.mark.django_db
def test_machine_sequence_detail_context(client):
    johns_hopkins = factories.InstitutionFactory.create(name="Johns Hopkins")
    group = factories.GroupFactory.create(name="Group", permissions=Permission.objects.all())
    current_user = factories.UserFactory.create(username='current_user', institution=johns_hopkins, groups=[group])

    dicom_series = factories.DicomSeriesFactory(zipped_dicom_files='data/dicom/006_mri_603A_UVA_Axial_2ME2SRS5.zip')

    machine_a = factories.MachineFactory(institution=current_user.institution)
    sequence_a = factories.SequenceFactory(institution=current_user.institution)
    machine_sequence_pair_a = factories.MachineSequencePairFactory(machine=machine_a, sequence=sequence_a)

    machine_b = factories.MachineFactory(institution=current_user.institution)
    sequence_b = factories.SequenceFactory(institution=current_user.institution)
    machine_sequence_pair_b = factories.MachineSequencePairFactory(machine=machine_b, sequence=sequence_b)

    factories.ScanFactory(
        creator=current_user,
        machine_sequence_pair=machine_sequence_pair_a,
        dicom_series=dicom_series,
        tolerance=2,
    )
    factories.ScanFactory(
        creator=current_user,
        machine_sequence_pair=machine_sequence_pair_b,
        dicom_series=dicom_series,
        tolerance=2,
    )

    client.force_login(current_user)

    res = client.get(reverse('machine_sequence_detail', args=(machine_sequence_pair_a.pk,)))
    scans = json.loads(res.context['scans'])
    for scan_data in scans:
        scan = Scan.objects.get(pk=scan_data['pk'])
        assert scan.machine_sequence_pair == machine_sequence_pair_a

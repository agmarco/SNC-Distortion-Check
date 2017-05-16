from unittest import mock
import pytest

from django.contrib.auth.models import Permission
from django.urls import reverse

from ..models import Scan
from .. import factories


@pytest.mark.django_db
def test_refresh_scan(client):
    johns_hopkins = factories.InstitutionFactory.create(name="Johns Hopkins")
    group = factories.GroupFactory.create(name="Group", permissions=Permission.objects.all())
    current_user = factories.UserFactory.create(username='current_user', institution=johns_hopkins, groups=[group])

    machine = factories.MachineFactory(institution=current_user.institution)
    sequence = factories.SequenceFactory(institution=current_user.institution)
    machine_sequence_pair = factories.MachineSequencePairFactory(
        machine=machine,
        sequence=sequence,
        tolerance=2,
    )

    old_golden_fiducials = factories.GoldenFiducialsFactory()
    new_golden_fiducials = factories.GoldenFiducialsFactory()
    phantom = factories.PhantomFactory(golden_fiducials=[old_golden_fiducials, new_golden_fiducials])
    new_golden_fiducials.activate()

    scan = factories.ScanFactory(
        creator=current_user,
        machine_sequence_pair=machine_sequence_pair,
        tolerance=1,
        golden_fiducials=old_golden_fiducials,
    )

    current_count = Scan.objects.count()

    client.force_login(current_user)

    with mock.patch('server.common.tasks.process_scan'):
        client.post(reverse('refresh_scan', args=(scan.pk,)))

    assert Scan.objects.count() == current_count + 1

    new_scan = Scan.objects.order_by('-last_modified_on').first()
    assert new_scan.tolerance == machine_sequence_pair.tolerance
    assert new_scan.golden_fiducials == phantom.active_gold_standard

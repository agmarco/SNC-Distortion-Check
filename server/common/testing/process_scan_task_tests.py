import unittest

import pytest

from ..tasks import process_scan
from .view_config import dicom_overlay_data
from ..factories import UserFactory, InstitutionFactory
import process.points_utils

# TODO: test how an unknown exception is handled; it should save an error
# message in scan.errors and should log the stack trace

@pytest.fixture
def scan():
    institution = InstitutionFactory(scans_remaining=100)
    user = UserFactory(institution=institution)
    scan = dicom_overlay_data(user)['scan']
    scan.tolerance = 4.0  # a large enough tolerance to ensure it passes
    scan.save()
    return scan


@pytest.mark.slow
@pytest.mark.django_db
def test_full_working_scan(scan):
    scans_remaining = scan.institution.scans_remaining
    assert scan.processing

    process_scan(scan.pk)
    scan.refresh_from_db()
    scan.institution.refresh_from_db()

    assert not scan.processing
    assert scan.errors is None
    assert scan.passed
    assert scan.raw_data
    assert scan.full_report
    assert scan.executive_report
    assert scan.institution.scans_remaining == scans_remaining - 1


@pytest.mark.slow
@pytest.mark.django_db
def test_scan_with_too_few_fiducials(scan):
    scans_remaining = scan.institution.scans_remaining

    def over_eager_remove_fps(points_ijk, voxels, voxel_spacing, phantom_model):
        return points_ijk[:5, :]

    assert not scan.full_report
    assert not scan.executive_report

    with unittest.mock.patch('process.fp_rejector.remove_fps', side_effect=over_eager_remove_fps):
        process_scan(scan.pk)

    scan.refresh_from_db()
    scan.institution.refresh_from_db()

    assert not scan.processing
    assert scan.errors is not None
    assert not scan.passed
    assert scan.raw_data
    assert not scan.full_report
    assert not scan.executive_report
    assert scan.institution.scans_remaining == scans_remaining


@pytest.mark.slow
@pytest.mark.django_db
def test_scan_with_too_low_TPF(scan):
    scans_remaining = scan.institution.scans_remaining

    def patched_metrics(FN_A_S, TP_A_S, TP_B, FP_B):
        _, FPF, FLE_percentiles = process.points_utils.metrics(FN_A_S, TP_A_S, TP_B, FP_B)
        return 0.5, FPF, FLE_percentiles

    with unittest.mock.patch('process.points_utils.metrics', patched_metrics):
        process_scan(scan.pk)

    scan.refresh_from_db()
    scan.institution.refresh_from_db()

    assert not scan.processing
    assert scan.errors is not None
    assert not scan.passed
    assert scan.raw_data
    assert not scan.full_report
    assert not scan.executive_report
    assert scan.institution.scans_remaining == scans_remaining

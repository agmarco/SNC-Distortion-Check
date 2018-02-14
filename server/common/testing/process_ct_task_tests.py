import unittest

import pytest
from django.core import files

from server.common.models import GoldenFiducials
from ..tasks import process_ct_upload
from ..factories import UserFactory, InstitutionFactory, PhantomFactory, GoldenFiducialsFactory, DicomSeriesFactory


@pytest.fixture
def ct():
    institution = InstitutionFactory()
    user = UserFactory(institution=institution)
    phantom = PhantomFactory(institution=user.institution)
    sample_603A_ct_zip_filename = 'data/dicom/001_ct_603A_E3148_ST1.25.zip'
    path = sample_603A_ct_zip_filename
    f = open(path, 'rb')
    content = files.File(f, name=path)
    dicom_series = DicomSeriesFactory(zipped_dicom_files=files.File(content.file, sample_603A_ct_zip_filename))
    golden_fiducials = GoldenFiducialsFactory(
        phantom=phantom,
        type=GoldenFiducials.CT,
        dicom_series=dicom_series,
        processing=True,
    )
    return golden_fiducials


@pytest.mark.slow
@pytest.mark.django_db
def test_full_working_ct(ct):
    assert ct.processing

    process_ct_upload(ct.pk)
    ct.refresh_from_db()

    assert not ct.processing
    assert ct.dicom_series
    assert ct.fiducials
    assert ct.errors is None


@pytest.mark.slow
@pytest.mark.django_db
def test_ct_with_too_few_fiducials(ct):
    def over_eager_remove_fps(points_ijk, voxels, voxel_spacing, phantom_model):
        return points_ijk[:5, :]

    with unittest.mock.patch('process.fp_rejector.remove_fps', side_effect=over_eager_remove_fps):
        process_ct_upload(ct.pk)
    ct.refresh_from_db()

    assert not ct.processing
    assert ct.errors is not None

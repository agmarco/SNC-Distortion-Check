import pytest

from ..tasks import process_scan
from .view_config import dicom_overlay_data
from ..factories import UserFactory, InstitutionFactory

# TODO: test how an unknown exception is handled; it should save an error
# message in scan.errors and should log the stack trace

# TODO: test how a timeout is handled; it should indicate that the timeout
# occurred to the user

# TODO: test how a known exception is handled; it should save a useful error
# message in scan.errors and should log the stack trace


@pytest.mark.slow
@pytest.mark.django_db
def test_working_scan():
    institution = InstitutionFactory()
    user = UserFactory(institution=institution)
    scan = dicom_overlay_data(user)['scan']

    assert scan.processing == True

    process_scan(scan.pk)
    scan.refresh_from_db()

    assert scan.processing == False
    assert scan.errors is None

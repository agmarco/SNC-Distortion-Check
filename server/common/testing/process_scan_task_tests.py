import pytest

from ..tasks import process_scan

# TODO: test how an unknown exception is handled; it should save an error
# message in scan.errors and should log the stack trace

# TODO: test how a timeout is handled; it should indicate that the timeout
# occurred to the user

# TODO: test how a known exception is handled; it should save a useful error
# message in scan.errors and should log the stack trace


@pytest.mark.django_db
def test_working_scan():
    # create a scan
    pass

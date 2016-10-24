import pytest

from testing import validate_case


def test_validate_assertions_rejects_at_least_at_most_conflict():
    with pytest.raises(ValueError):
        validate_assertions({'at_least': 5, 'at_most': 10})


def test_validate_assertions_rejects_same_with_other_condition():
    with pytest.raises(ValueError):
        validate_assertions({'same': True, 'at_most': 10})


def test_validate_assertions_rejects_at_least_and_at_least_percent():
    '''
    It doesn't make sense to include both of these
    '''
    with pytest.raises(ValueError):
        validate_assertions({'at_least': 0.5, 'at_least_percent': 10})

from enum import Enum

import pytest
import itertools

from datetime import datetime, timedelta
from django.contrib.auth.models import Permission

from .. import factories
from ..models import Global


def _powerset(iterable):
    s = list(iterable)
    return itertools.chain.from_iterable(itertools.combinations(s, r) for r in range(len(s) + 1))


@pytest.fixture(params=(_powerset(permission[0] for permission in Global._meta.permissions)))
def permissions_data(db, request):
    johns_hopkins = factories.InstitutionFactory.create(name="Johns Hopkins")
    group = factories.GroupFactory.create(name="Group")
    for permission in request.param:
        group.permissions.add(Permission.objects.get(codename=permission))
    current_user = factories.UserFactory.create(email='current_user@johnshopkins.edu', institution=johns_hopkins, groups=[group])

    return {
        'current_user': current_user,
    }


@pytest.fixture(params=(True, False))
def institution_data(db, request):
    johns_hopkins = factories.InstitutionFactory.create(name="Johns Hopkins")
    utexas = factories.InstitutionFactory.create(name="University of Texas")
    group = factories.GroupFactory.create(name="Group", permissions=Permission.objects.all())
    current_user = factories.UserFactory.create(email='current_user@johnshopkins.edu', institution=johns_hopkins, groups=[group])

    return {
        'current_user': current_user,
        'institution': johns_hopkins if request.param else utexas,
    }


@pytest.fixture(params=('GET', 'POST'))
def http_method_data(db, request):
    johns_hopkins = factories.InstitutionFactory.create(name="Johns Hopkins")
    group = factories.GroupFactory.create(name="Group", permissions=Permission.objects.all())
    current_user = factories.UserFactory.create(email='current_user@johnshopkins.edu', institution=johns_hopkins, groups=[group])

    return {
        'current_user': current_user,
        'method': request.param,
    }


class License(Enum):
    VALID = 1
    NULL = 2
    EXPIRED = 3
    NO_REMAINING_SCANS = 4


@pytest.fixture(params=list(License))
def license_data(db, request):
    johns_hopkins = factories.InstitutionFactory.create(name="Johns Hopkins")
    group = factories.GroupFactory.create(name="Group", permissions=Permission.objects.all())
    current_user = factories.UserFactory.create(email='current_user@johnshopkins.edu', institution=johns_hopkins,
                                                groups=[group])
    if request.param == License.VALID:
        johns_hopkins.license_expiration_date = datetime.now().date() + timedelta(days=1)
        johns_hopkins.scans_remaining = 1
        johns_hopkins.save()
    elif request.param == License.EXPIRED:
        johns_hopkins.license_expiration_date = datetime.now().date() - timedelta(days=1)
        johns_hopkins.scans_remaining = 1
        johns_hopkins.save()
    elif request.param == License.NO_REMAINING_SCANS:
        johns_hopkins.license_expiration_date = datetime.now().date() + timedelta(days=1)
        johns_hopkins.scans_remaining = 0
        johns_hopkins.save()

    return {
        'current_user': current_user,
    }

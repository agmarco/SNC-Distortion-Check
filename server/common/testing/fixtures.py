import pytest
import itertools

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

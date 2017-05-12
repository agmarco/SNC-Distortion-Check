import pytest

from django.contrib.auth.models import Permission

from .. import factories
from ..models import Global


# TODO this will not cover views that require more than one permission.
@pytest.fixture(params=(None, *(permission[0] for permission in Global._meta.permissions)))
def permissions_data(db, request):
    johns_hopkins = factories.InstitutionFactory.create(name="Johns Hopkins")
    group = factories.GroupFactory.create(name="Group")

    if request.param:
        group.permissions.add(Permission.objects.get(codename=request.param))
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

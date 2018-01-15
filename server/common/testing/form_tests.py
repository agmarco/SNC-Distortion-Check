import pytest

from django.contrib.auth.models import Permission

from .. import factories
from ..forms import CreateMachineForm


@pytest.mark.django_db
def test_create_machine_form(client):
    johns_hopkins = factories.InstitutionFactory.create(name="Johns Hopkins")
    group = factories.GroupFactory.create(name="Group", permissions=Permission.objects.all())
    current_user = factories.UserFactory.create(email='current_user@johnshopkins.edu', institution=johns_hopkins, groups=[group])

    client.force_login(current_user)

    data = {'name': "Machine Name", 'model': "Machine Model", 'manufacturer': "Machine Manufacturer"}

    form = CreateMachineForm(data=data, institution=current_user.institution)
    assert form.is_valid()
    form.save()

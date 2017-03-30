import pytest
import json

from django.contrib.auth.models import Permission
from django.urls import reverse

from .. import factories


@pytest.mark.django_db
def test_validate_serial(client):
    johns_hopkins = factories.InstitutionFactory.create(name="Johns Hopkins")
    group = factories.GroupFactory.create(name="Group", permissions=Permission.objects.all())
    phantom_model = factories.PhantomModelFactory(name='CIRS 603A', model_number='603A')
    initial_phantom = factories.PhantomFactory(model=phantom_model, serial_number='A123')
    current_user = factories.UserFactory.create(username='current_user', institution=johns_hopkins, groups=[group])

    client.force_login(current_user)

    res = client.post(reverse('validate_serial'), {'serial_number': 'wrong'})
    content = json.loads(res.content)
    assert not content['valid']

    res = client.post(reverse('validate_serial'), {'serial_number': initial_phantom.serial_number})
    content = json.loads(res.content)
    assert content['valid'] and content['model_number'] == initial_phantom.model.model_number

import pytest

from django.urls import reverse
from django.contrib.auth.models import Permission

from server.common import factories
from server.common.models import Phantom, GoldenFiducials


@pytest.mark.django_db
def test_phantoms(client):
    johns_hopkins = factories.InstitutionFactory.create(name="Johns Hopkins")
    group = factories.GroupFactory.create(name="Group", permissions=Permission.objects.all())
    phantom_model = factories.PhantomModelFactory(name='CIRS 603A', model_number='603A')
    initial_phantom = factories.PhantomFactory(model=phantom_model, serial_number='A123')
    current_user = factories.UserFactory.create(username='current_user', institution=johns_hopkins, groups=[group])

    client.force_login(current_user)
    client.post(reverse('create_phantom'), {
        'name': 'Create Phantom',
        'serial_number': initial_phantom.serial_number,
    })
    phantom = Phantom.objects.order_by('-last_modified_on').first()

    # check that a GoldenFiducials was created and activated
    assert phantom.goldenfiducials_set.count() == 1
    assert phantom.goldenfiducials_set.first().is_active
    assert phantom.active_gold_standard.fiducials == phantom.model.cad_fiducials

    # test that changing the cad_fiducials of the phantom model doesn't change the CAD gold standard for the phantom
    phantom_model_fiducials = phantom.model.cad_fiducials
    phantom.model.cad_fiducials = factories.FiducialsFactory()
    phantom.model.save()
    assert phantom.active_gold_standard.fiducials == phantom_model_fiducials


@pytest.mark.django_db
def test_gold_standards(client):
    johns_hopkins = factories.InstitutionFactory.create(name="Johns Hopkins")
    group = factories.GroupFactory.create(name="Group", permissions=Permission.objects.all())
    current_user = factories.UserFactory.create(username='current_user', institution=johns_hopkins, groups=[group])
    phantom = factories.PhantomFactory()
    cad_gold_standard = phantom.active_gold_standard
    raw_gold_standard = factories.GoldenFiducialsFactory(phantom=phantom, type=GoldenFiducials.CSV)
    raw_gold_standard.activate()

    client.force_login(current_user)

    # the CAD gold standard should not be deletable even when inactive:
    assert client.post(reverse('delete_gold_standard', args=(phantom.pk, cad_gold_standard.pk))).status_code == 403

    # the CSV gold standard should not be deletable when active:
    assert client.post(reverse('delete_gold_standard', args=(phantom.pk, raw_gold_standard.pk))).status_code == 403

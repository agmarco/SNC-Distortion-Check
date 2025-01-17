import pytest
import numpy as np

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
    current_user = factories.UserFactory.create(email='current_user@johnshopkins.edu', institution=johns_hopkins, groups=[group])

    client.force_login(current_user)

    # check that a request with an invalid serial number doesn't create a new phantom
    current_count = Phantom.objects.count()
    client.post(reverse('create_phantom'), {
        'name': 'Create Phantom',
        'serial_number': 'wrong',
    })
    assert Phantom.objects.count() == current_count

    # send a request with a valid serial number
    client.post(reverse('create_phantom'), {
        'name': 'Create Phantom',
        'serial_number': initial_phantom.serial_number,
    })
    phantom = Phantom.objects.order_by('-last_modified_on').first()

    # check that a GoldenFiducials was created and activated
    assert phantom.goldenfiducials_set.count() == 1
    assert phantom.goldenfiducials_set.first().is_active

    phantom_fiducials = phantom.active_gold_standard.fiducials.fiducials

    # check that the CAD gold standard for the phantom has the same fiducials as the phantom model
    assert np.allclose(phantom_fiducials, phantom.model.cad_fiducials.fiducials)

    # check that editing the cad_fiducials of the phantom model doesn't change the CAD gold standard fiducials for the phantom
    phantom.model.cad_fiducials.fiducials = np.random.rand(3, 10)
    phantom.model.cad_fiducials.save()
    assert np.allclose(phantom.active_gold_standard.fiducials.fiducials, phantom_fiducials)

    # check that replacing the cad_fiducials of the phantom model doesn't change the CAD gold standard fiducials for the phantom
    phantom.model.cad_fiducials = factories.FiducialsFactory()
    phantom.model.save()
    assert np.allclose(phantom.active_gold_standard.fiducials.fiducials, phantom_fiducials)


@pytest.mark.django_db
def test_gold_standards(client):
    johns_hopkins = factories.InstitutionFactory.create(name="Johns Hopkins")
    group = factories.GroupFactory.create(name="Group", permissions=Permission.objects.all())
    current_user = factories.UserFactory.create(email='current_user@johnshopkins.edu', institution=johns_hopkins, groups=[group])
    phantom = factories.PhantomFactory()
    cad_gold_standard = phantom.active_gold_standard
    raw_gold_standard = factories.GoldenFiducialsFactory(phantom=phantom, type=GoldenFiducials.CSV)
    raw_gold_standard.activate()

    client.force_login(current_user)

    # the CAD gold standard should not be deletable even when inactive:
    assert client.post(reverse('delete_gold_standard', args=(phantom.pk, cad_gold_standard.pk))).status_code == 403

    # other gold standards should not be deletable when active:
    assert client.post(reverse('delete_gold_standard', args=(phantom.pk, raw_gold_standard.pk))).status_code == 403

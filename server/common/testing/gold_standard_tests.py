import csv
import io
import os

import pytest
import numpy as np

from django.conf import settings
from django.contrib.auth.models import Permission
from django.test import Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from .. import factories
from ..forms import UploadCTForm


@pytest.mark.django_db
def test_upload_ct():
    johns_hopkins = factories.InstitutionFactory.create(name="Johns Hopkins")
    group = factories.GroupFactory.create(name="Group", permissions=Permission.objects.all())
    current_user = factories.UserFactory.create(username='current_user', institution=johns_hopkins, groups=[group])

    client = Client()
    client.force_login(current_user)

    # MRI archive should not be valid
    with open(os.path.join(settings.BASE_DIR, 'data/dicom/006_mri_603A_UVA_Axial_2ME2SRS5.zip'), 'rb') as file:
        form = UploadCTForm(files={'dicom_archive': SimpleUploadedFile(file.name, file.read(), 'application/zip')})
        assert not form.is_valid()

    # CT archive should be valid
    with open(os.path.join(settings.BASE_DIR, 'data/dicom/004_ct_603A_UVA_IYKOQG2M.zip'), 'rb') as file:
        form = UploadCTForm(files={'dicom_archive': SimpleUploadedFile(file.name, file.read(), 'application/zip')})
        assert form.is_valid()


@pytest.mark.django_db
def test_upload_csv():
    johns_hopkins = factories.InstitutionFactory.create(name="Johns Hopkins")
    group = factories.GroupFactory.create(name="Group", permissions=Permission.objects.all())
    current_user = factories.UserFactory.create(username='current_user', institution=johns_hopkins, groups=[group])
    phantom = factories.PhantomFactory(institution=johns_hopkins)

    client = Client()
    client.force_login(current_user)

    fiducials = np.random.randint(0, 100, (5, 5))
    csv_content = io.StringIO()
    writer = csv.writer(csv_content)
    for row in fiducials.T:
        writer.writerow(row)

    client.post(reverse('upload_raw', args=(phantom.pk,)), {'csv': SimpleUploadedFile('file.csv', csv_content.getvalue().encode(), 'text/csv')})

    # check that a new gold standard was created
    assert phantom.goldenfiducials_set.count() == 2

    # check that the new gold standard contains the right fiducials
    gold_standard = phantom.goldenfiducials_set.order_by('-last_modified_on').first()
    assert np.array_equal(gold_standard.fiducials.fiducials, fiducials)

    # check that the generated csv contains the right fiducials:
    response = client.get(reverse('gold_standard_csv', args=(phantom.pk, gold_standard.pk)))
    assert np.array_equal(np.genfromtxt(SimpleUploadedFile('file.csv', response.content, 'text/csv'), delimiter=',').T, fiducials)

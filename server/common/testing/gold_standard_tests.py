import csv
import io
import os
from unittest import mock

import pytest
import numpy as np

from django.conf import settings
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from .. import factories
from ..forms import UploadCtForm, UploadRawForm


def _generate_csv(ndarray):
    csv_content = io.StringIO()
    writer = csv.writer(csv_content)
    for row in ndarray:
        writer.writerow(row)
    return csv_content


@pytest.mark.django_db
def test_upload_ct(client):
    johns_hopkins = factories.InstitutionFactory.create(name="Johns Hopkins")
    group = factories.GroupFactory.create(name="Group", permissions=Permission.objects.all())
    current_user = factories.UserFactory.create(email='current_user@johnshopkins.edu', institution=johns_hopkins, groups=[group])
    phantom = factories.PhantomFactory(institution=johns_hopkins)
    goldenfiducials_count = phantom.goldenfiducials_set.count()

    client.force_login(current_user)

    post_data = {
        'dicom_archive_url': 'http://localhost',
        'dicom_archive': 'arbitrary.zip',
    }
    url = reverse('upload_ct', args=(phantom.pk,))
    with mock.patch('server.common.views.process_ct_upload'):
        client.post(url, post_data)

    # check that a new gold standard was created and that it is processing
    assert phantom.goldenfiducials_set.count() == goldenfiducials_count + 1
    gold_standard = phantom.goldenfiducials_set.order_by('-last_modified_on').first()
    assert gold_standard.processing


@pytest.mark.django_db
def test_upload_csv(client):
    johns_hopkins = factories.InstitutionFactory.create(name="Johns Hopkins")
    group = factories.GroupFactory.create(name="Group", permissions=Permission.objects.all())
    current_user = factories.UserFactory.create(email='current_user@johnshopkins.edu', institution=johns_hopkins, groups=[group])
    phantom = factories.PhantomFactory(institution=johns_hopkins)

    client.force_login(current_user)

    url = reverse('upload_raw', args=(phantom.pk,))
    fiducials = np.random.rand(3, 10)
    csv_content = _generate_csv(fiducials.T)
    post_data = {'csv': SimpleUploadedFile('file.csv', csv_content.getvalue().encode(), 'text/csv')}
    client.post(url, post_data)

    # check that a new gold standard was created
    assert phantom.goldenfiducials_set.count() == 2

    # check that the new gold standard contains the right fiducials
    gold_standard = phantom.goldenfiducials_set.order_by('-last_modified_on').first()
    assert np.allclose(gold_standard.fiducials.fiducials, fiducials)

    # check that the generated csv contains the right fiducials:
    response = client.get(reverse('gold_standard_csv', args=(phantom.pk, gold_standard.pk)))
    fiducials_array = np.genfromtxt(SimpleUploadedFile('file.csv', response.content, 'text/csv'), delimiter=',').T
    assert np.allclose(fiducials_array, fiducials)


@pytest.mark.django_db
def test_upload_ct_form(client):
    johns_hopkins = factories.InstitutionFactory.create(name="Johns Hopkins")
    group = factories.GroupFactory.create(name="Group", permissions=Permission.objects.all())
    current_user = factories.UserFactory.create(email='current_user@johnshopkins.edu', institution=johns_hopkins, groups=[group])

    client.force_login(current_user)

    form = UploadCtForm(data={
        'dicom_archive_url': 'http://localhost',
        'dicom_archive': 'arbitrary.zip',
    })
    assert form.is_valid()


@pytest.mark.django_db
def test_upload_raw_form(client):
    johns_hopkins = factories.InstitutionFactory.create(name="Johns Hopkins")
    group = factories.GroupFactory.create(name="Group", permissions=Permission.objects.all())
    current_user = factories.UserFactory.create(email='current_user@johnshopkins.edu', institution=johns_hopkins, groups=[group])

    client.force_login(current_user)

    # swapped axes should not be valid
    fiducials = np.random.rand(10, 3)
    csv_content = _generate_csv(fiducials.T)
    form = UploadRawForm(files={'csv': SimpleUploadedFile('file.csv', csv_content.getvalue().encode(), 'text/csv')})
    assert not form.is_valid()

    # CSV with typo should not be valid
    fiducials = np.random.rand(3, 10)
    str_fiducials = np.array([[str(i) for i in row] for row in fiducials])
    str_fiducials[1, 1] = '2.5q'
    csv_content = _generate_csv(str_fiducials.T)
    form = UploadRawForm(files={'csv': SimpleUploadedFile('file.csv', csv_content.getvalue().encode(), 'text/csv')})
    assert not form.is_valid()

    # TODO CSV with duplicate points should not be valid

    # valid CSV
    fiducials = np.random.rand(3, 10)
    csv_content = _generate_csv(fiducials.T)
    form = UploadRawForm(files={'csv': SimpleUploadedFile('file.csv', csv_content.getvalue().encode(), 'text/csv')})
    assert form.is_valid()

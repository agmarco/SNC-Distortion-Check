import pytest

from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.management import call_command


@pytest.mark.django_db
def test_configuration_permissions():
    call_command('generate_dev_data')

    client = Client()
    url = reverse('configuration')

    # non-medical-physicist user unauthorized
    current_user = get_user_model().objects.get(username='therapist')
    client.force_login(current_user)
    response = client.get(url)
    assert response.status_code == 403

    # medical-physicist user authorized
    current_user = get_user_model().objects.get(username='medical_physicist')
    client.force_login(current_user)
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_configuration_context():
    call_command('generate_dev_data')

    client = Client()
    url = reverse('configuration')

    current_user = get_user_model().objects.get(username='medical_physicist')
    client.force_login(current_user)
    response = client.get(url)

    phantoms = response.context['phantoms']
    machines = response.context['machines']
    sequences = response.context['sequences']
    users = response.context['users']

    # only display items from the user's institution
    assert all([phantom.institution.pk == current_user.institution.pk for phantom in phantoms])
    assert all([machine.institution.pk == current_user.institution.pk for machine in machines])
    assert all([sequence.institution.pk == current_user.institution.pk for sequence in sequences])
    assert all([user.institution.pk == current_user.institution.pk for user in users])

    # don't display deleted items
    assert all([not phantom.deleted for phantom in phantoms])
    assert all([not machine.deleted for machine in machines])
    assert all([not sequence.deleted for sequence in sequences])
    assert all([not user.deleted for user in users])

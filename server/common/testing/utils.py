from django.db import models
from django.test import Client


def _validate_fields(model, data):
    for field_name in data.keys():

        # if the field is a foreign key, check that the primary key equals the POST data
        if isinstance(model._meta.get_field(field_name), models.ForeignKey):
            assert getattr(model, field_name).pk == int(data[field_name])
        else:
            assert getattr(model, field_name) == data[field_name]


def validate_create_view(user, url, model_class, data):
    """
    Send a POST request to the specified url, and assert that a model is created with the provided data.
    """

    current_count = model_class.objects.count()

    client = Client()
    client.force_login(user)
    client.post(url, data=data)

    assert model_class.objects.count() == current_count + 1
    model = model_class.objects.all().order_by('-last_modified_on').first()
    _validate_fields(model, data)
    assert model.institution == user.institution

    return model


def validate_update_view(user, url, model_class, data):
    """
    Send a POST request to the specified url, and assert that a model is updated with the provided data.
    """

    current_count = model_class.objects.count()

    client = Client()
    client.force_login(user)
    client.post(url, data=data)

    assert model_class.objects.count() == current_count
    model = model_class.objects.all().order_by('-last_modified_on').first()
    _validate_fields(model, data)

    return model


def validate_delete_view(user, url, model_class):
    """
    Send a POST request to the specified url, and assert that a model's 'deleted' attribute is set to True
    but that no models are actually deleted.
    """

    current_count = model_class.objects.count()

    client = Client()
    client.force_login(user)
    client.post(url)

    assert model_class.objects.count() == current_count
    model = model_class.objects.all().order_by('-last_modified_on').first()
    assert model.deleted

    return model


def assert_can_get(user, urls):
    """
    Assert that the url returns a 200 or 302 for GET requests.
    """

    client = Client()
    client.force_login(user)
    assert all(client.get(url).status_code in (200, 302) for url in urls)


def assert_can_post(user, urls):
    """
    Assert that the url returns a 200 or 302 for POST requests.
    """

    client = Client()
    client.force_login(user)
    assert all(client.post(url).status_code in (200, 302) for url in urls)


def assert_cannot_get(user, urls):
    """
    Assert that the url returns a 403 for GET requests.
    """

    client = Client()
    client.force_login(user)
    assert all(client.get(url).status_code == 403 for url in urls)


def assert_cannot_post(user, urls):
    """
    Assert that the url returns a 403 for POST requests.
    """

    client = Client()
    client.force_login(user)

    assert all(client.post(url).status_code == 403 for url in urls)


def assert_can_view(user, urls):
    """
    Assert that the url returns a 200, 302, or 405 for GET and POST requests.
    """

    client = Client()
    client.force_login(user)

    for url in urls:
        assert client.get(url).status_code in (200, 302, 405)
        assert client.post(url).status_code in (200, 302, 405)


def assert_cannot_view(user, urls):
    """
   Assert that the url returns a 403 or 405 for GET and POST requests.
   """

    client = Client()
    client.force_login(user)

    for url in urls:
        assert client.get(url).status_code in (403, 405)
        assert client.post(url).status_code in (403, 405)

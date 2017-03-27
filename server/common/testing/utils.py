from django.db import models
from django.test import Client


def _validate_fields(model, data):
    for field_name in data.keys():

        # if the field is a foreign key, check that the primary key equals the POST data
        if isinstance(model._meta.get_field(field_name), models.ForeignKey):
            assert getattr(model, field_name).pk == int(data[field_name])
        else:
            assert getattr(model, field_name) == data[field_name]


def validate_create_view(user, url, model_class, data=None):
    current_count = model_class.objects.count()

    client = Client()
    client.force_login(user)
    client.post(url, data=data)

    assert model_class.objects.count() == current_count + 1
    model = model_class.objects.all().order_by('-last_modified_on').first()
    _validate_fields(model, data)
    assert model.institution == user.institution

    return model


def validate_update_view(user, url, model_class, data=None):
    current_count = model_class.objects.count()

    client = Client()
    client.force_login(user)
    client.post(url, data=data)

    assert model_class.objects.count() == current_count
    model = model_class.objects.all().order_by('-last_modified_on').first()
    _validate_fields(model, data)

    return model


def validate_delete_view(user, url, model_class, data=None):
    current_count = model_class.objects.count()

    client = Client()
    client.force_login(user)
    client.post(url, data=data)

    assert model_class.objects.count() == current_count
    model = model_class.objects.all().order_by('-last_modified_on').first()
    assert model.deleted

    return model

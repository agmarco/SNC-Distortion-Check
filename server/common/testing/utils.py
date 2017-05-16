from contextlib import ExitStack
from unittest import mock

from django.db import models


def _validate_fields(model, data):
    for field_name in data.keys():

        # if the field is a foreign key, check that the primary key equals the POST data
        if isinstance(model._meta.get_field(field_name), models.ForeignKey):
            assert getattr(model, field_name).pk == int(data[field_name])
        else:
            assert getattr(model, field_name) == data[field_name]


def validate_create_view(client, user, url, model_class, data=None, patches=None):
    current_count = model_class.objects.count()

    client.force_login(user)
    get_response(client, url, 'POST', data, patches)

    assert model_class.objects.count() == current_count + 1
    model = model_class.objects.order_by('-last_modified_on').first()
    _validate_fields(model, data)

    if hasattr(model, 'institution'):
        assert model.institution == user.institution
    return model


def validate_update_view(client, user, url, model_class, data=None, patches=None):
    current_count = model_class.objects.count()

    client.force_login(user)
    get_response(client, url, 'POST', data, patches)

    assert model_class.objects.count() == current_count
    model = model_class.objects.order_by('-last_modified_on').first()
    _validate_fields(model, data)

    return model


def validate_delete_view(client, user, url, model_class, data=None, patches=None):
    current_count = model_class.objects.count()

    client.force_login(user)
    get_response(client, url, 'POST', data, patches)

    assert model_class.objects.count() == current_count
    model = model_class.objects.order_by('-last_modified_on').first()
    assert model.deleted

    return model


def allowed_access(client, url, method, data, patches=None):
    return get_response(client, url, method, data, patches).status_code in (200, 302)


def denied_access(client, url, method, data, patches=None):
    return get_response(client, url, method, data, patches).status_code in (403, 405)


def get_response(client, url, method, data, patches=None):
    # TODO patches not working
    # it appears that in order for the patches to work, reverse() must be called with the context manager?
    if patches:
        with ExitStack() as stack:
            for manager in map(mock.patch, patches):
                stack.enter_context(manager)
            return getattr(client, method.lower())(url, data)
    else:
        return getattr(client, method.lower())(url, data)

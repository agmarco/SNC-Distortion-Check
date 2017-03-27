from django.urls import reverse

from .. import views
from .. import factories
from ..models import Phantom, GoldenFiducials, Machine, Sequence, User

# This is the configuration for the view tests. Each configuration dict may contain the following keys:
# 'view': the view object.
# 'data': a function that returns a dict containing additional data that is needed for the test.
# 'crud': a 3-tuple containing:
#     (1) a string representing the type of CRUD operation.
#     (2) the model class.
#     (3) a dict containing the POST data for the request. This can also be a function that returns a dict, in which
#         case it will receive the data specified by the 'data' key as an argument.
# 'url': the url for the view. This can also be a function that returns the url, in which case it will receive the data
#     specified by the 'data' key as an argument.
# 'permissions': a list of permissions that are required to access the view.
# 'validate_institution': a boolean representing whether the user's institution must be validated against the view.
# 'methods': a list of the HTTP methods that should be tested.


class Crud:
    CREATE = 'CREATE'
    UPDATE = 'UPDATE'
    DELETE = 'DELETE'


def delete_gold_standard_data():
    phantom = factories.PhantomFactory()
    gold_standard = factories.GoldenFiducialsFactory(phantom=phantom, type=GoldenFiducials.RAW)
    return {
        'phantom': phantom,
        'gold_standard': gold_standard,
    }


def activate_gold_standard_data():
    phantom = factories.PhantomFactory()
    gold_standard = factories.GoldenFiducialsFactory(phantom=phantom, type=GoldenFiducials.RAW)
    return {
        'phantom': phantom,
        'gold_standard': gold_standard,
    }


def gold_standard_csv_data():
    phantom = factories.PhantomFactory()
    gold_standard = factories.GoldenFiducialsFactory(phantom=phantom, type=GoldenFiducials.RAW)
    return {
        'phantom': phantom,
        'gold_standard': gold_standard,
    }

VIEWS = (
    {
        'view': views.upload_file,
        'url': reverse('upload_file'),
        'permissions': ('common.configuration',),
        'validate_institution': False,
        'methods': ('GET', 'POST'),
    },
    {
        'view': views.Configuration,
        'url': reverse('configuration'),
        'permissions': ('common.configuration',),
        'validate_institution': False,
        'methods': ('GET',),
    },
    {
        'view': views.CreatePhantom,
        'data': lambda: {'phantom_model': factories.PhantomModelFactory(name='CIRS 603A', model_number='603A')},
        'crud': (Crud.CREATE, Phantom, lambda data: {
            'name': 'Create Phantom',
            'model': str(data['phantom_model'].pk),
            'serial_number': '12345',
        }),
        'url': reverse('create_phantom'),
        'permissions': ('common.configuration',),
        'validate_institution': False,
        'methods': ('GET', 'POST'),
    },
    {
        'view': views.UpdatePhantom,
        'data': lambda: {'phantom': factories.PhantomFactory()},
        'crud': (Crud.UPDATE, Phantom, {'name': 'Update Phantom'}),
        'url': lambda data: reverse('update_phantom', args=(data['phantom'].pk,)),
        'permissions': ('common.configuration',),
        'validate_institution': True,
        'methods': ('GET', 'POST'),
    },
    {
        'view': views.DeletePhantom,
        'data': lambda: {'phantom': factories.PhantomFactory()},
        'crud': (Crud.DELETE, Phantom, None),
        'url': lambda data: reverse('delete_phantom', args=(data['phantom'].pk,)),
        'permissions': ('common.configuration',),
        'validate_institution': True,
        'methods': ('GET', 'POST'),
    },
    {
        'view': views.UploadCT,
        'data': lambda: {'phantom': factories.PhantomFactory()},
        'url': lambda data: reverse('upload_ct', args=(data['phantom'].pk,)),
        'permissions': ('common.configuration',),
        'validate_institution': True,
        'methods': ('GET', 'POST'),
    },
    {
        'view': views.UploadRaw,
        'data': lambda: {'phantom': factories.PhantomFactory()},
        'url': lambda data: reverse('upload_raw', args=(data['phantom'].pk,)),
        'permissions': ('common.configuration',),
        'validate_institution': True,
        'methods': ('GET', 'POST'),
    },
    {
        'view': views.DeleteGoldStandard,
        'data': delete_gold_standard_data,
        'crud': (Crud.DELETE, GoldenFiducials, None),
        'url': lambda data: reverse('delete_gold_standard', args=(data['phantom'].pk, data['gold_standard'].pk)),
        'permissions': ('common.configuration',),
        'validate_institution': True,
        'methods': ('GET', 'POST'),
    },
    {
        'view': views.activate_gold_standard,
        'data': activate_gold_standard_data,
        'url': lambda data: reverse('activate_gold_standard', args=(data['phantom'].pk, data['gold_standard'].pk)),
        'permissions': ('common.configuration',),
        'validate_institution': True,
        'methods': ('POST',),
    },
    {
        'view': views.gold_standard_csv,
        'data': gold_standard_csv_data,
        'url': lambda data: reverse('gold_standard_csv', args=(data['phantom'].pk, data['gold_standard'].pk)),
        'permissions': ('common.configuration',),
        'validate_institution': True,
        'methods': ('GET',),
    },
    {
        'view': views.CreateMachine,
        'crud': (Crud.CREATE, Machine, {
            'name': 'Create Machine',
            'model': 'Create Model',
            'manufacturer': 'Create Manufacturer',
        }),
        'url': reverse('create_machine'),
        'permissions': ('common.configuration',),
        'validate_institution': False,
        'methods': ('GET', 'POST'),
    },
    {
        'view': views.UpdateMachine,
        'data': lambda: {'machine': factories.MachineFactory()},
        'crud': (Crud.UPDATE, Machine, {
            'name': 'Update Machine',
            'model': 'Update Model',
            'manufacturer': 'Update Manufacturer',
        }),
        'url': lambda data: reverse('update_machine', args=(data['machine'].pk,)),
        'permissions': ('common.configuration',),
        'validate_institution': True,
        'methods': ('GET', 'POST'),
    },
    {
        'view': views.DeleteMachine,
        'data': lambda: {'machine': factories.MachineFactory()},
        'crud': (Crud.DELETE, Machine, None),
        'url': lambda data: reverse('delete_machine', args=(data['machine'].pk,)),
        'permissions': ('common.configuration',),
        'validate_institution': True,
        'methods': ('GET', 'POST'),
    },
    {
        'view': views.CreateSequence,
        'crud': (Crud.CREATE, Sequence, {
            'name': 'Create Sequence',
            'instructions': 'Create Instructions',
        }),
        'url': reverse('create_sequence'),
        'permissions': ('common.configuration',),
        'validate_institution': False,
        'methods': ('GET', 'POST'),
    },
    {
        'view': views.UpdateSequence,
        'data': lambda: {'sequence': factories.SequenceFactory()},
        'crud': (Crud.UPDATE, Sequence, {
            'name': 'Update Sequence',
            'instructions': 'Update Instructions',
        }),
        'url': lambda data: reverse('update_sequence', args=(data['sequence'].pk,)),
        'permissions': ('common.configuration',),
        'validate_institution': True,
        'methods': ('GET', 'POST'),
    },
    {
        'view': views.DeleteSequence,
        'data': lambda: {'sequence': factories.SequenceFactory()},
        'crud': (Crud.DELETE, Sequence, None),
        'url': lambda data: reverse('delete_sequence', args=(data['sequence'].pk,)),
        'permissions': ('common.configuration',),
        'validate_institution': True,
        'methods': ('GET', 'POST'),
    },
    {
        'view': views.CreateUser,
        'crud': (Crud.CREATE, User, {
            'username': 'create_user',
            'first_name': 'Create First Name',
            'last_name': 'Create Last Name',
            'email': 'create_user@example.com',
        }),
        'url': reverse('create_user'),
        'permissions': ('common.manage_users',),
        'validate_institution': False,
        'methods': ('GET', 'POST'),
    },
    {
        'view': views.DeleteUser,
        'data': lambda: {'user': factories.UserFactory()},
        'crud': (Crud.DELETE, User, None),
        'url': lambda data: reverse('delete_user', args=(data['user'].pk,)),
        'permissions': ('common.manage_users',),
        'validate_institution': True,
        'methods': ('GET', 'POST'),
    },
)

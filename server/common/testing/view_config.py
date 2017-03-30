from django.urls import reverse

from .. import views
from .. import api
from .. import factories
from ..models import Phantom, GoldenFiducials, Machine, Sequence, User

# This is the configuration for the view tests. Each configuration dict may contain the following keys:
# 'view': the view object.
# 'data': a function that returns a dict containing additional data that is needed for the tests. It receives the
#     current user as an argument.
# 'crud': a 3-tuple containing:
#     (1) a string representing the type of CRUD operation.
#     (2) the model class.
#     (3) a dict containing the POST data for the request. This can also be a function that returns a dict, in which
#         case it will receive the data specified by the 'data' key as an argument.
# 'url': the url for the view. This can also be a function that receives the data specified by the 'data' key and
# returns the url.
# 'permissions': a list of permissions that are required to access the view.
# 'validate_institution': a boolean representing whether the user's institution must be validated against the view.
# 'methods': a dict containing as keys the HTTP methods that should be tested, and as values the GET or POST data to
# send with the request. The values may also be functions that receive the data specified by the 'data' key and return
# the GET or POST data.

# TODO need a way of specifying POST data


class Crud:
    CREATE = 'CREATE'
    UPDATE = 'UPDATE'
    DELETE = 'DELETE'


def create_phantom_data(user):
    phantom_model = factories.PhantomModelFactory(name='CIRS 603A', model_number='603A')
    phantom = factories.PhantomFactory(model=phantom_model, serial_number='A123')
    return {
        'phantom_model': phantom_model,
        'phantom': phantom,
    }


def machine_sequence_detail_data(user):
    machine = factories.MachineFactory(institution=user.institution)
    sequence = factories.SequenceFactory()
    machine_sequence_pair = factories.MachineSequencePairFactory(machine=machine, sequence=sequence)
    return {
        'machine': machine,
        'sequence': sequence,
        'machine_sequence_pair': machine_sequence_pair,
    }


def delete_gold_standard_data(user):
    phantom = factories.PhantomFactory(institution=user.institution)
    gold_standard = factories.GoldenFiducialsFactory(phantom=phantom, type=GoldenFiducials.CSV)
    return {
        'phantom': phantom,
        'gold_standard': gold_standard,
    }


def activate_gold_standard_data(user):
    phantom = factories.PhantomFactory(institution=user.institution)
    gold_standard = factories.GoldenFiducialsFactory(phantom=phantom, type=GoldenFiducials.CSV)
    return {
        'phantom': phantom,
        'gold_standard': gold_standard,
    }


def gold_standard_csv_data(user):
    phantom = factories.PhantomFactory(institution=user.institution)
    gold_standard = factories.GoldenFiducialsFactory(phantom=phantom, type=GoldenFiducials.CSV)
    return {
        'phantom': phantom,
        'gold_standard': gold_standard,
    }

VIEWS = (
    {
        'view': views.landing,
        'url': reverse('landing'),
        'permissions': ('common.configuration',),
        'validate_institution': False,
        'methods': {'GET': None},
    },
    {
        'view': views.Configuration,
        'url': reverse('configuration'),
        'permissions': ('common.configuration',),
        'validate_institution': False,
        'methods': {'GET': None},
    },
    {
        'view': views.machine_sequences,
        'url': reverse('landing'),
        'permissions': ('common.configuration',),
        'validate_institution': False,
        'methods': {'GET': None},
    },
    {
        'view': views.MachineSequenceDetail,
        'data': machine_sequence_detail_data,
        'url': lambda data: reverse('machine_sequence_detail', args=(data['machine_sequence_pair'].pk,)),
        'permissions': ('common.configuration',),
        'validate_institution': True,
        'methods': {'GET': None},
    },
    {
        'view': views.upload_scan,
        'url': reverse('upload_scan'),
        'permissions': ('common.configuration',),
        'validate_institution': False,
        'methods': {'GET': None, 'POST': None},
    },
    {
        'view': views.CreatePhantom,
        'data': create_phantom_data,
        'crud': (Crud.CREATE, Phantom, lambda data: {
            'name': 'Create Phantom',
            'serial_number': 'A123',
        }),
        'url': reverse('create_phantom'),
        'permissions': ('common.configuration',),
        'validate_institution': False,
        'methods': {'GET': None, 'POST': None},
    },
    {
        'view': views.UpdatePhantom,
        'data': lambda user: {'phantom': factories.PhantomFactory(institution=user.institution)},
        'crud': (Crud.UPDATE, Phantom, {'name': 'Update Phantom'}),
        'url': lambda data: reverse('update_phantom', args=(data['phantom'].pk,)),
        'permissions': ('common.configuration',),
        'validate_institution': True,
        'methods': {'GET': None, 'POST': None},
    },
    {
        'view': views.DeletePhantom,
        'data': lambda user: {'phantom': factories.PhantomFactory(institution=user.institution)},
        'crud': (Crud.DELETE, Phantom, None),
        'url': lambda data: reverse('delete_phantom', args=(data['phantom'].pk,)),
        'permissions': ('common.configuration',),
        'validate_institution': True,
        'methods': {'GET': None, 'POST': None},
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
        'methods': {'GET': None, 'POST': None},
    },
    {
        'view': views.UpdateMachine,
        'data': lambda user: {'machine': factories.MachineFactory(institution=user.institution)},
        'crud': (Crud.UPDATE, Machine, {
            'name': 'Update Machine',
            'model': 'Update Model',
            'manufacturer': 'Update Manufacturer',
        }),
        'url': lambda data: reverse('update_machine', args=(data['machine'].pk,)),
        'permissions': ('common.configuration',),
        'validate_institution': True,
        'methods': {'GET': None, 'POST': None},
    },
    {
        'view': views.DeleteMachine,
        'data': lambda user: {'machine': factories.MachineFactory(institution=user.institution)},
        'crud': (Crud.DELETE, Machine, None),
        'url': lambda data: reverse('delete_machine', args=(data['machine'].pk,)),
        'permissions': ('common.configuration',),
        'validate_institution': True,
        'methods': {'GET': None, 'POST': None},
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
        'methods': {'GET': None, 'POST': None},
    },
    {
        'view': views.UpdateSequence,
        'data': lambda user: {'sequence': factories.SequenceFactory(institution=user.institution)},
        'crud': (Crud.UPDATE, Sequence, {
            'name': 'Update Sequence',
            'instructions': 'Update Instructions',
        }),
        'url': lambda data: reverse('update_sequence', args=(data['sequence'].pk,)),
        'permissions': ('common.configuration',),
        'validate_institution': True,
        'methods': {'GET': None, 'POST': None},
    },
    {
        'view': views.DeleteSequence,
        'data': lambda user: {'sequence': factories.SequenceFactory(institution=user.institution)},
        'crud': (Crud.DELETE, Sequence, None),
        'url': lambda data: reverse('delete_sequence', args=(data['sequence'].pk,)),
        'permissions': ('common.configuration',),
        'validate_institution': True,
        'methods': {'GET': None, 'POST': None},
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
        'methods': {'GET': None, 'POST': None},
    },
    {
        'view': views.DeleteUser,
        'data': lambda user: {'user': factories.UserFactory(institution=user.institution)},
        'crud': (Crud.DELETE, User, None),
        'url': lambda data: reverse('delete_user', args=(data['user'].pk,)),
        'permissions': ('common.manage_users',),
        'validate_institution': True,
        'methods': {'GET': None, 'POST': None},
    },
{
        'view': views.UploadCT,
        'data': lambda user: {'phantom': factories.PhantomFactory(institution=user.institution)},
        'url': lambda data: reverse('upload_ct', args=(data['phantom'].pk,)),
        'permissions': ('common.configuration',),
        'validate_institution': True,
        'methods': {'GET': None, 'POST': None},
    },
    {
        'view': views.UploadRaw,
        'data': lambda user: {'phantom': factories.PhantomFactory(institution=user.institution)},
        'url': lambda data: reverse('upload_raw', args=(data['phantom'].pk,)),
        'permissions': ('common.configuration',),
        'validate_institution': True,
        'methods': {'GET': None, 'POST': None},
    },
    {
        'view': views.DeleteGoldStandard,
        'data': delete_gold_standard_data,
        'crud': (Crud.DELETE, GoldenFiducials, None),
        'url': lambda data: reverse('delete_gold_standard', args=(data['phantom'].pk, data['gold_standard'].pk)),
        'permissions': ('common.configuration',),
        'validate_institution': True,
        'methods': {'GET': None, 'POST': None},
    },
    {
        'view': views.activate_gold_standard,
        'data': activate_gold_standard_data,
        'url': lambda data: reverse('activate_gold_standard', args=(data['phantom'].pk, data['gold_standard'].pk)),
        'permissions': ('common.configuration',),
        'validate_institution': True,
        'methods': {'POST': None},
    },
    {
        'view': views.gold_standard_csv,
        'data': gold_standard_csv_data,
        'url': lambda data: reverse('gold_standard_csv', args=(data['phantom'].pk, data['gold_standard'].pk)),
        'permissions': ('common.configuration',),
        'validate_institution': True,
        'methods': {'GET': None},
    },
    {
        'view': api.ValidateSerial,
        'data': lambda user: {'phantom': factories.PhantomFactory(serial_number='A123')},
        'url': lambda data: reverse('validate_serial'),
        'permissions': ('common.configuration',),
        'validate_institution': False,
        'methods': {'POST': lambda data: {'serial_number': data['phantom'].serial_number}},
    },
)

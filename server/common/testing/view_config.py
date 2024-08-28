from enum import Enum, auto
from typing import NamedTuple, Union, Callable, Dict, Any, Tuple, List, Type, Optional, TypeVar

from django.contrib.auth.tokens import default_token_generator
from django.db.models import Model
from django.http import HttpRequest
from django.http.response import HttpResponseBase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views import View

from .. import views
from .. import api
from .. import factories
from ..models import Phantom, GoldenFiducials, Machine, Sequence, User

# TODO: add institution_required config option

# Getting this to work will require recursive type aliases:
# https://github.com/python/mypy/issues/731
JsonPayload = Any

ViewData = Dict[str, Any]


class Crud(Enum):
    CREATE = auto()
    UPDATE = auto()
    DELETE = auto()


V = TypeVar('V', bound=View)
M = TypeVar('M', bound=Model)


class ViewConfig(NamedTuple):
    # The view object.
    view: Union[Type[V], Callable[[HttpRequest], HttpResponseBase]]

    # A boolean representing whether the view is tested.
    exclude: bool = None

    # A function that returns a dict containing additional data that is needed for the tests. It
    # receives the current user as an argument.
    data: Callable[[User], ViewData] = None

    # A 3-tuple containing:
    #     (1) the type of CRUD operation,
    #     (2) the model class,
    #     (3) a dict containing the POST data for the request. This can also be a function that
    #         returns a dict, in which case it will receive the data specified by the 'data' key as
    #         an argument.
    crud: Tuple[
        Crud,
        Type[M],
        Optional[Union[JsonPayload, Callable[[ViewData], JsonPayload]]],
    ] = None

    # The url for the view. This can also be a function that receives the data specified by the
    # 'data' key and returns the url.
    url: Union[str, Callable[[ViewData], str]] = None

    # A boolean representing whether the user must be authenticated.
    login_required: bool = None

    # A list of permissions that are required to access the view.
    permissions: List[str] = None

    # A boolean representing whether the user's institution must be validated against the view.
    validate_institution: bool = None

    # A boolean representing whether an institution's license, if it exists, must be unexpired to
    # view this page.
    check_license: bool = None

    # A boolean representing whether the number of remaining scans for an institutions's license,
    # if it exists, must be greater than 0 to view this page.
    check_scans: bool = None

    # A dict containing as keys the HTTP methods that should be tested, and as values the
    # GET or POST data to send with the request. The values may also be functions that receive the
    # data specified by the 'data' key and return the GET or POST data.
    methods: Dict[str, Union[JsonPayload, Callable[[ViewData], JsonPayload]]] = None

    # A list of strings representing objects to be patched by unittest.mock
    patches: List[str] = None


def machine_sequence_detail_data(user: User) -> ViewData:
    machine = factories.MachineFactory(institution=user.institution)
    sequence = factories.SequenceFactory()
    machine_sequence_pair = factories.MachineSequencePairFactory(machine=machine, sequence=sequence)
    return {
        'machine_sequence_pair': machine_sequence_pair,
    }


def delete_gold_standard_data(user: User) -> ViewData:
    phantom = factories.PhantomFactory(institution=user.institution)
    gold_standard = factories.GoldenFiducialsFactory(phantom=phantom, type=GoldenFiducials.CSV)
    return {
        'phantom': phantom,
        'gold_standard': gold_standard,
    }


def activate_gold_standard_data(user: User) -> ViewData:
    phantom = factories.PhantomFactory(institution=user.institution)
    gold_standard = factories.GoldenFiducialsFactory(phantom=phantom, type=GoldenFiducials.CSV)
    return {
        'phantom': phantom,
        'gold_standard': gold_standard,
    }


def gold_standard_csv_data(user: User) -> ViewData:
    phantom = factories.PhantomFactory(institution=user.institution)
    gold_standard = factories.GoldenFiducialsFactory(phantom=phantom, type=GoldenFiducials.CSV)
    return {
        'phantom': phantom,
        'gold_standard': gold_standard,
    }


def scan_errors_data(user: User) -> ViewData:
    machine = factories.MachineFactory(institution=user.institution)
    sequence = factories.SequenceFactory(institution=user.institution)
    machine_sequence_pair = factories.MachineSequencePairFactory(machine=machine, sequence=sequence)
    scan = factories.ScanFactory(
        creator=user,
        machine_sequence_pair=machine_sequence_pair,
        tolerance=2,
    )
    return {
        'scan': scan,
    }


def gold_standard_errors_data(user: User) -> ViewData:
    phantom = factories.PhantomFactory(institution=user.institution)
    golden_fiducials = factories.GoldenFiducialsFactory(phantom=phantom, type=GoldenFiducials.CT)
    return {
        'phantom': phantom,
        'golden_fiducials': golden_fiducials,
    }


def delete_scan_data(user: User) -> ViewData:
    machine = factories.MachineFactory(institution=user.institution)
    sequence = factories.SequenceFactory(institution=user.institution)
    machine_sequence_pair = factories.MachineSequencePairFactory(machine=machine, sequence=sequence)
    scan = factories.ScanFactory(
        creator=user,
        machine_sequence_pair=machine_sequence_pair,
        tolerance=2,
    )
    return {
        'scan': scan,
    }


def dicom_overlay_data(user: User) -> ViewData:
    machine = factories.MachineFactory(institution=user.institution)
    sequence = factories.SequenceFactory(institution=user.institution)
    machine_sequence_pair = factories.MachineSequencePairFactory(machine=machine, sequence=sequence)
    scan = factories.ScanFactory(
        creator=user,
        machine_sequence_pair=machine_sequence_pair,
        tolerance=2,
    )
    return {
        'scan': scan,
    }


def refresh_scan_data(user: User) -> ViewData:
    machine = factories.MachineFactory(institution=user.institution)
    sequence = factories.SequenceFactory(institution=user.institution)
    machine_sequence_pair = factories.MachineSequencePairFactory(machine=machine, sequence=sequence)
    scan = factories.ScanFactory(
        creator=user,
        machine_sequence_pair=machine_sequence_pair,
        tolerance=2,
    )
    return {
        'scan': scan,
    }


def update_tolerance_data(user: User) -> ViewData:
    machine = factories.MachineFactory(institution=user.institution)
    sequence = factories.SequenceFactory(institution=user.institution)
    machine_sequence_pair = factories.MachineSequencePairFactory(machine=machine, sequence=sequence)
    return {
        'machine_sequence_pair': machine_sequence_pair,
    }


def poll_scans_data(user: User) -> ViewData:
    machine = factories.MachineFactory(institution=user.institution)
    sequence = factories.SequenceFactory(institution=user.institution)
    machine_sequence_pair = factories.MachineSequencePairFactory(machine=machine, sequence=sequence)
    scan = factories.ScanFactory(
        creator=user,
        machine_sequence_pair=machine_sequence_pair,
    )
    return {
        'machine_sequence_pair': machine_sequence_pair,
        'scan': scan,
    }


def poll_ct_data(user: User) -> ViewData:
    phantom = factories.PhantomFactory(institution=user.institution)
    golden_fiducials = factories.GoldenFiducialsFactory(phantom=phantom, type=GoldenFiducials.CT)

    return {
        'phantom': phantom,
        'golden_fiducials': golden_fiducials,
    }


def raw_data_data(user: User) -> ViewData:
    machine = factories.MachineFactory(institution=user.institution)
    sequence = factories.SequenceFactory(institution=user.institution)
    machine_sequence_pair = factories.MachineSequencePairFactory(machine=machine, sequence=sequence)

    scan = factories.ScanFactory(
        creator=user,
        machine_sequence_pair=machine_sequence_pair,
        tolerance=2,
    )
    return {
        'scan': scan,
    }


def create_password_data(user: User) -> ViewData:
    new_user = factories.UserFactory.create(email='new_user@johnshopkins.edu')
    uid = urlsafe_base64_encode(force_bytes(new_user.pk))
    token = default_token_generator.make_token(new_user)
    return {
        'uid': uid,
        'token': token,
    }


def create_user_data(user: User) -> ViewData:
    factories.GroupFactory.create(name="Manager")
    return {}


def register_data(user: User) -> ViewData:
    factories.GroupFactory.create(name="Manager")
    return {'phantom': factories.PhantomFactory(serial_number='SN1')}


VIEWS = [
    ViewConfig(
        view=views.LandingView,
        url=reverse('landing'),
        login_required=True,
        permissions=[],
        validate_institution=False,
        check_license=True,
        check_scans=False,
        methods={'GET': None},
    ), ViewConfig(
        view=views.ConfigurationView,
        url=reverse('configuration'),
        login_required=True,
        permissions=['common.configuration'],
        validate_institution=False,
        check_license=True,
        check_scans=False,
        methods={'GET': None, 'POST': None},
    ), ViewConfig(
        view=views.MachineSequenceDetailView,
        data=machine_sequence_detail_data,
        url=lambda data: reverse('machine_sequence_detail', args=[data['machine_sequence_pair'].pk]),
        login_required=True,
        permissions=[],
        validate_institution=True,
        check_license=True,
        check_scans=False,
        methods={'GET': None},
    ), ViewConfig(
        view=views.UploadScanView,
        url=reverse('upload_scan'),
        login_required=True,
        permissions=[],
        validate_institution=False,
        check_license=True,
        check_scans=True,
        methods={'GET': None, 'POST': None},
        patches=['server.common.views.process_scan'],
    ), ViewConfig(
        view=views.DeleteScanView,
        data=delete_scan_data,
        url=lambda data: reverse('delete_scan', args=[data['scan'].pk]),
        login_required=True,
        permissions=[],
        validate_institution=True,
        check_license=True,
        check_scans=False,
        methods={'GET': None, 'POST': None},
    ), ViewConfig(
        view=views.ScanErrorsView,
        data=scan_errors_data,
        url=lambda data: reverse('scan_errors', args=[data['scan'].pk]),
        login_required=True,
        permissions=[],
        validate_institution=True,
        check_license=True,
        check_scans=False,
        methods={'GET': None},
    ), ViewConfig(
        view=views.GoldStandardErrorsView,
        data=gold_standard_errors_data,
        url=lambda data: reverse('gold_standard_errors', args=[
            data['phantom'].pk,
            data['golden_fiducials'].pk,
        ]),
        login_required=True,
        permissions=[],
        validate_institution=True,
        check_license=True,
        check_scans=False,
        methods={'GET': None},
    ), ViewConfig(
        view=views.CreatePhantomView,
        url=reverse('create_phantom'),
        login_required=True,
        permissions=['common.configuration'],
        validate_institution=False,
        check_license=True,
        check_scans=False,
        methods={'GET': None, 'POST': None},
    ), ViewConfig(
        view=views.UpdatePhantomView,
        data=lambda user: {'phantom': factories.PhantomFactory(institution=user.institution)},
        crud=(Crud.UPDATE, Phantom, {'name': 'Update Phantom'}),
        url=lambda data: reverse('update_phantom', args=[data['phantom'].pk]),
        login_required=True,
        permissions=['common.configuration'],
        validate_institution=True,
        check_license=True,
        check_scans=False,
        methods={'GET': None, 'POST': None},
    ), ViewConfig(
        view=views.DeletePhantomView,
        data=lambda user: {'phantom': factories.PhantomFactory(institution=user.institution)},
        crud=(Crud.DELETE, Phantom, None),
        url=lambda data: reverse('delete_phantom', args=[data['phantom'].pk]),
        login_required=True,
        permissions=['common.configuration'],
        validate_institution=True,
        check_license=True,
        check_scans=False,
        methods={'GET': None, 'POST': None},
    ), ViewConfig(
        view=views.CreateMachineView,
        crud=(Crud.CREATE, Machine, {
            'name': 'Create Machine',
            'model': 'Create Model',
            'manufacturer': 'Create Manufacturer',
        }),
        url=reverse('create_machine'),
        login_required=True,
        permissions=['common.configuration'],
        validate_institution=False,
        check_license=True,
        check_scans=False,
        methods={'GET': None, 'POST': None},
    ), ViewConfig(
        view=views.UpdateMachineView,
        data=lambda user: {'machine': factories.MachineFactory(institution=user.institution)},
        crud=(Crud.UPDATE, Machine, {
            'name': 'Update Machine',
            'model': 'Update Model',
            'manufacturer': 'Update Manufacturer',
        }),
        url=lambda data: reverse('update_machine', args=[data['machine'].pk]),
        login_required=True,
        permissions=['common.configuration'],
        validate_institution=True,
        check_license=True,
        check_scans=False,
        methods={'GET': None, 'POST': None},
    ), ViewConfig(
        view=views.DeleteMachineView,
        data=lambda user: {'machine': factories.MachineFactory(institution=user.institution)},
        crud=(Crud.DELETE, Machine, None),
        url=lambda data: reverse('delete_machine', args=[data['machine'].pk]),
        login_required=True,
        permissions=['common.configuration'],
        validate_institution=True,
        check_license=True,
        check_scans=False,
        methods={'GET': None, 'POST': None},
    ), ViewConfig(
        view=views.CreateSequenceView,
        crud=(Crud.CREATE, Sequence, {
            'name': 'Create Sequence',
            'instructions': 'Create Instructions',
            'tolerance': 4.0,
        }),
        url=reverse('create_sequence'),
        login_required=True,
        permissions=['common.configuration'],
        validate_institution=False,
        check_license=True,
        check_scans=False,
        methods={'GET': None, 'POST': None},
    ), ViewConfig(
        view=views.UpdateSequenceView,
        data=lambda user: {'sequence': factories.SequenceFactory(institution=user.institution)},
        crud=(Crud.UPDATE, Sequence, {
            'name': 'Update Sequence',
            'instructions': 'Update Instructions',
            'tolerance': 4.0,
        }),
        url=lambda data: reverse('update_sequence', args=[data['sequence'].pk]),
        login_required=True,
        permissions=['common.configuration'],
        validate_institution=True,
        check_license=True,
        check_scans=False,
        methods={'GET': None, 'POST': None},
    ), ViewConfig(
        view=views.DeleteSequenceView,
        data=lambda user: {'sequence': factories.SequenceFactory(institution=user.institution)},
        crud=(Crud.DELETE, Sequence, None),
        url=lambda data: reverse('delete_sequence', args=[data['sequence'].pk]),
        login_required=True,
        permissions=['common.configuration'],
        validate_institution=True,
        check_license=True,
        check_scans=False,
        methods={'GET': None, 'POST': None},
    ), ViewConfig(
        view=views.CreateUserView,
        data=create_user_data,
        crud=(Crud.CREATE, User, {
            'first_name': 'Create First Name',
            'last_name': 'Create Last Name',
            'email': 'create_user@example.com',
            'user_type': "Manager",
        }),
        url=reverse('create_user'),
        login_required=True,
        permissions=['common.manage_users'],
        validate_institution=False,
        check_license=True,
        check_scans=False,
        methods={'GET': None, 'POST': None},
    ), ViewConfig(
        view=views.DeleteUserView,
        data=lambda user: {'user': factories.UserFactory(institution=user.institution)},
        crud=(Crud.DELETE, User, None),
        url=lambda data: reverse('delete_user', args=[data['user'].pk]),
        login_required=True,
        permissions=['common.manage_users'],
        validate_institution=True,
        check_license=True,
        check_scans=False,
        methods={'GET': None, 'POST': None},
    ), ViewConfig(
        view=views.UploadCtView,
        data=lambda user: {'phantom': factories.PhantomFactory(institution=user.institution)},
        url=lambda data: reverse('upload_ct', args=[data['phantom'].pk]),
        login_required=True,
        permissions=['common.configuration'],
        validate_institution=True,
        check_license=True,
        check_scans=True,
        methods={'GET': None, 'POST': None},
        patches=['server.common.views.process_ct_upload'],
    ), ViewConfig(
        view=views.UploadRawView,
        data=lambda user: {'phantom': factories.PhantomFactory(institution=user.institution)},
        url=lambda data: reverse('upload_raw', args=[data['phantom'].pk]),
        login_required=True,
        permissions=['common.configuration'],
        validate_institution=True,
        check_license=True,
        check_scans=False,
        methods={'GET': None, 'POST': None},
    ), ViewConfig(
        view=views.DeleteGoldStandardView,
        data=delete_gold_standard_data,
        crud=(Crud.DELETE, GoldenFiducials, None),
        url=lambda data: reverse('delete_gold_standard', args=[
            data['phantom'].pk,
            data['gold_standard'].pk,
        ]),
        login_required=True,
        permissions=['common.configuration'],
        validate_institution=True,
        check_license=True,
        check_scans=False,
        methods={'GET': None, 'POST': None},
    ), ViewConfig(
        view=views.ActivateGoldStandardView,
        data=activate_gold_standard_data,
        url=lambda data: reverse('activate_gold_standard', args=[
            data['phantom'].pk,
            data['gold_standard'].pk,
        ]),
        login_required=True,
        permissions=['common.configuration'],
        validate_institution=True,
        check_license=True,
        check_scans=False,
        methods={'POST': None},
    ), ViewConfig(
        view=views.GoldStandardCsvView,
        data=gold_standard_csv_data,
        url=lambda data: reverse('gold_standard_csv', args=[
            data['phantom'].pk,
            data['gold_standard'].pk,
        ]),
        login_required=True,
        permissions=['common.configuration'],
        validate_institution=True,
        check_license=True,
        check_scans=False,
        methods={'GET': None},
    ), ViewConfig(
        view=views.DicomOverlayView,
        data=dicom_overlay_data,
        url=lambda data: reverse('dicom_overlay', args=[data['scan'].pk]),
        login_required=True,
        permissions=[],
        validate_institution=True,
        check_license=True,
        check_scans=False,
        methods={'GET': None, 'POST': None},
    ), ViewConfig(
        view=views.DicomOverlaySuccessView,
        data=dicom_overlay_data,
        url=lambda data: reverse('dicom_overlay_success', args=[data['scan'].pk]),
        login_required=True,
        permissions=[],
        validate_institution=True,
        check_license=True,
        check_scans=False,
        methods={'GET': None},
    ), ViewConfig(
        view=views.refresh_scan_view,
        data=refresh_scan_data,
        url=lambda data: reverse('refresh_scan', args=[data['scan'].pk]),
        login_required=True,
        permissions=[],
        validate_institution=True,
        check_license=True,
        check_scans=True,
        methods={'POST': None},
        patches=['server.common.views.process_scan'],
    ), ViewConfig(
        view=views.TermsOfUseView,
        url=reverse('terms_of_use'),
        login_required=False,
        permissions=[],
        validate_institution=False,
        check_license=False,
        check_scans=False,
        methods={'GET': None},
    ), ViewConfig(
        view=views.PrivacyPolicyView,
        url=reverse('privacy_policy'),
        login_required=False,
        permissions=[],
        validate_institution=False,
        check_license=False,
        check_scans=False,
        methods={'GET': None},
    ), ViewConfig(
        view=views.AccountView,
        url=reverse('account'),
        login_required=True,
        permissions=[],
        validate_institution=False,
        check_license=True,
        check_scans=False,
        crud=(Crud.UPDATE, User, {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'email': 'update@email.com',
        }),
        methods={'GET': None, 'POST': None},
    ), ViewConfig(
        view=views.RegisterView,
        data=register_data,
        url=reverse('register'),
        login_required=False,
        permissions=[],
        validate_institution=False,
        check_license=False,
        check_scans=False,
        methods={'GET': None, 'POST': lambda data: {
            'phantom_serial_number': data['phantom'].serial_number,
            'institution_name': 'Johns Hopkins',
            'institution_address': '3101 Wyman Park Dr.\nBaltimore, MD 21211',
            'institution_phone': '555-555-5555',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'johndoe@johnshopkins.edu',
            'email_repeat': 'johndoe@johnshopkins.edu',
        }},
    ), ViewConfig(
        view=views.RegisterDoneView,
        url=reverse('register_done'),
        login_required=False,
        permissions=[],
        validate_institution=False,
        check_license=False,
        check_scans=False,
        methods={'GET': None},
    ), ViewConfig(
        view=views.CreatePasswordView,
        data=create_password_data,
        url=lambda data: reverse('create_password', args=[data['uid'], data['token']]),
        login_required=False,
        permissions=[],
        validate_institution=False,
        check_license=False,
        check_scans=False,
        methods={'GET': None, 'POST': None},
    ), ViewConfig(
        view=views.CreatePasswordCompleteView,
        url=reverse('create_password_complete'),
        login_required=False,
        permissions=[],
        validate_institution=False,
        check_license=False,
        check_scans=False,
        methods={'GET': None},
    ), ViewConfig(
        view=views.fake_server_error,
        exclude=True,
    ), ViewConfig(
        view=api.ValidateSerialView,
        data=lambda user: {'phantom': factories.PhantomFactory(serial_number='SN1')},
        url=reverse('validate_serial'),
        login_required=False,
        permissions=[],
        validate_institution=False,
        check_license=False,
        check_scans=False,
        methods={'POST': lambda data: {'serial_number': data['phantom'].serial_number}},
    ), ViewConfig(
        view=api.UpdateToleranceView,
        data=update_tolerance_data,
        url=reverse('update_tolerance'),
        login_required=True,
        permissions=['common.configuration'],
        validate_institution=True,
        check_license=True,
        check_scans=False,
        methods={'POST': lambda data: {
            'pk': data['machine_sequence_pair'].pk,
            'tolerance': 1,
        }},
    ), ViewConfig(
        view=api.PollScansView,
        data=poll_scans_data,
        url=reverse('poll_scans'),
        login_required=True,
        permissions=[],
        validate_institution=True,
        check_license=True,
        check_scans=False,
        methods={'POST': lambda data: {
            'machine_sequence_pair_pk': data['machine_sequence_pair'].pk,
            'scan_pks': [data['scan'].pk],
        }},
    ), ViewConfig(
        view=api.PollCtView,
        data=poll_ct_data,
        url=reverse('poll_ct'),
        login_required=True,
        permissions=[],
        validate_institution=True,
        check_license=True,
        check_scans=False,
        methods={'POST': lambda data: {
            'phantom_pk': data['phantom'].pk,
            'golden_fiducials_pks': [data['golden_fiducials'].pk],
        }},
    ), ViewConfig(
        view=api.UploadAsDev,
        exclude=True,
    ), ViewConfig(
        view=api.SignS3View,
        url=reverse('sign_s3'),
        login_required=True,
        permissions=[],
        validate_institution=False,
        check_license=True,
        check_scans=True,
        methods={'GET': {
            'file_name': 'test.txt',
            'file_type': 'text/plain',
        }},
    )
]

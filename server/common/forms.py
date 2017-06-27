import zipfile
from functools import partial

from django import forms

import numpy as np
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError

from process import dicom_import
from .models import Phantom, Institution, User, Machine, Sequence
from .validators import validate_phantom_serial_number


class CirsFormMixin:
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super(CirsFormMixin, self).__init__(*args, **kwargs)


class AccountForm(CirsFormMixin, forms.ModelForm):
    email = forms.EmailField(help_text=None)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')


class CreatePhantomForm(CirsFormMixin, forms.Form):
    name = forms.CharField()
    serial_number = forms.CharField(validators=[validate_phantom_serial_number])

    def save(self, institution=None, commit=True):
        if self.errors:
            raise ValueError(f"""The Phantom could not be created because the data didn't validate.""")

        phantom = Phantom.objects.get(serial_number=self.cleaned_data['serial_number'])
        phantom.name = self.cleaned_data['name']
        phantom.deleted = False
        if institution:
            phantom.institution = institution
        if commit:
            phantom.save()
        return phantom


class UploadScanForm(CirsFormMixin, forms.Form):
    machine = forms.IntegerField()
    sequence = forms.IntegerField()
    phantom = forms.IntegerField()
    dicom_archive = forms.FileField(label="MRI Scan Files")
    notes = forms.CharField(required=False)

    def clean_dicom_archive(self):
        try:
            dicom_import.combined_series_from_zip(self.cleaned_data['dicom_archive'])
        except dicom_import.DicomImportException as e:
            raise forms.ValidationError(e.args[0])

        with zipfile.ZipFile(self.cleaned_data['dicom_archive'], 'r') as zip_file:
            datasets = dicom_import.dicom_datasets_from_zip(zip_file)

        self.cleaned_data['datasets'] = datasets
        return self.cleaned_data['dicom_archive']


class UploadCtForm(CirsFormMixin, forms.Form):
    dicom_archive = forms.FileField(label="File Browser")

    def clean_dicom_archive(self):
        try:
            dicom_import.combined_series_from_zip(self.cleaned_data['dicom_archive'])
        except dicom_import.DicomImportException as e:
            raise forms.ValidationError(e.args[0])

        with zipfile.ZipFile(self.cleaned_data['dicom_archive'], 'r') as zip_file:
            datasets = dicom_import.dicom_datasets_from_zip(zip_file)

        ds = datasets[0]
        if not hasattr(ds, 'SeriesInstanceUID'):
            raise ValidationError("The DICOM files must contain the 'SeriesInstanceUID'.")
        if not hasattr(ds, 'StudyInstanceUID'):
            raise ValidationError("The DICOM files must contain the 'StudyInstanceUID'.")
        if not hasattr(ds, 'PatientID'):
            raise ValidationError("The DICOM files must contain the 'PatientID'.")

        self.cleaned_data['datasets'] = datasets
        return self.cleaned_data['dicom_archive']


class UploadRawForm(CirsFormMixin, forms.Form):
    csv = forms.FileField(label="File Browser")

    @staticmethod
    def _has_duplicates(ndarray):

        # TODO
        return False

    def clean_csv(self):
        try:
            fiducials = np.genfromtxt(self.cleaned_data['csv'], delimiter=',').T
        except ValueError:
            raise forms.ValidationError("The file is not formatted properly.")

        if np.isnan(fiducials).any():
            raise forms.ValidationError("The file is not formatted properly. Some of the cells are invalid.")

        if fiducials.shape[0] != 3:
            if fiducials.shape[1] == 3:
                raise forms.ValidationError("The file contains three rows instead of three columns.")
            else:
                raise forms.ValidationError("The file must have three columns (x, y, and z).")

        if self._has_duplicates(fiducials):
            raise forms.ValidationError("The file contains duplicate points.")

        self.cleaned_data['fiducials'] = fiducials
        return self.cleaned_data['csv']


class InstitutionForm(CirsFormMixin, forms.ModelForm):
    class Meta:
        model = Institution
        fields = ('name', 'address', 'phone_number')
        labels = {
            'name': "Institution Name",
            'address': "Institution Address",
            'phone_number': "Institution Contact Phone Number",
        }


class DicomOverlayForm(CirsFormMixin, forms.Form):
    study_instance_uid = forms.CharField(label="StudyInstanceUID", required=False)
    patient_id = forms.CharField(label="PatientID", required=False)
    isocenter_x = forms.FloatField(label="x", widget=forms.NumberInput(attrs={'step': '0.01'}), required=False)
    isocenter_y = forms.FloatField(label="y", widget=forms.NumberInput(attrs={'step': '0.01'}), required=False)
    isocenter_z = forms.FloatField(label="z", widget=forms.NumberInput(attrs={'step': '0.01'}), required=False)
    frame_of_reference_uid = forms.CharField(label="FrameOfReferenceUID", required=False)


class CreatePasswordForm(CirsFormMixin, PasswordResetForm):
    def get_users(self, email):
        active_users = User.objects.filter(email__iexact=email, is_active=True)
        return (u for u in active_users if not u.has_usable_password())


class BaseUserForm(CirsFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs):
        self.create_password_form = None
        self.save_m2m = None
        super(BaseUserForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(BaseUserForm, self).clean()
        self.create_password_form = CreatePasswordForm({'email': cleaned_data.get('email')})
        if not self.create_password_form.is_valid():
            raise ValidationError("""Something went wrong. Please try again, or contact CIRS support if the problem
                                  persists.""")
        return cleaned_data

    def save(self, commit=True, **kwargs):
        if self.errors:
            raise ValueError(f"""The {self.instance._meta.object_name} could not be
                             {'created' if self.instance._state.adding else 'changed'} because the data didn't
                             validate.""")

        self.instance.set_unusable_password()
        if commit:
            # If committing, save the instance and the m2m data immediately.
            self.instance.save()
            self._save_m2m(**kwargs)
        else:
            # If not committing, add a method to the form to allow deferred saving of m2m data.
            self.save_m2m = partial(self._save_m2m, **kwargs)
        return self.instance

    def _save_m2m(self, **kwargs):
        super(BaseUserForm, self)._save_m2m()
        self.create_password_form.save(**kwargs)


class CreateUserForm(BaseUserForm):
    MANAGER = "Manager"
    MEDICAL_PHYSICIST = "Medical Physicist"
    THERAPIST = "Therapist"
    GROUP_CHOICES = (
        (MANAGER, "Manager"),
        (MEDICAL_PHYSICIST, "Medical Physicist"),
        (THERAPIST, "Therapist"),
    )

    field_order = (
        'first_name',
        'last_name',
        'email',
        'user_type',
    )

    user_type_ht = """The user type determines what permissions the account will have. Therapist users can upload
                new MR scans for analysis. Medical Physicist users can do everything therapists can do, and can also
                add and configure phantoms, machines, and sequences. Managers can do everything Medical Physicists
                can do, and can also add and delete new users. Please note that once a user type is set, it cannot be
                changed (except by CIRS support)."""
    user_type = forms.ChoiceField(choices=GROUP_CHOICES, widget=forms.RadioSelect, help_text=user_type_ht)

    class Meta(BaseUserForm.Meta):
        fields = ('first_name', 'last_name', 'email', 'user_type')

    def save(self, institution=None, **kwargs):
        if institution:
            self.instance.institution = institution
        return super(CreateUserForm, self).save(**kwargs)

    def _save_m2m(self, **kwargs):
        super(CreateUserForm, self)._save_m2m(**kwargs)
        self.instance.groups.add(Group.objects.get(name=self.cleaned_data['user_type']))


class RegisterForm(BaseUserForm):
    phantom_serial_number = forms.CharField(validators=[validate_phantom_serial_number])
    institution_name = forms.CharField()
    institution_address = forms.CharField()
    institution_phone = forms.CharField(label="Institution Contact Phone Number")
    email_repeat = forms.EmailField()

    class Meta(BaseUserForm.Meta):
        fields = (
            'phantom_serial_number',
            'institution_name',
            'institution_address',
            'institution_phone',
            'first_name',
            'last_name',
            'email',
            'email_repeat',
        )

    def clean(self):
        cleaned_data = super(RegisterForm, self).clean()
        email = cleaned_data.get('email')
        email_repeat = cleaned_data.get('email_repeat')

        if email != email_repeat:
            raise ValidationError("Emails do not match.")
        return cleaned_data

    def save(self, **kwargs):
        institution = Institution.objects.create(name=self.cleaned_data['institution_name'],
                                                 address=self.cleaned_data['institution_address'],
                                                 phone_number=self.cleaned_data['institution_phone'])
        phantom = Phantom.objects.get(serial_number=self.cleaned_data['phantom_serial_number'])
        phantom.institution = institution
        phantom.save()
        self.instance.institution = institution
        return super(RegisterForm, self).save(**kwargs)

    def _save_m2m(self, **kwargs):
        super(RegisterForm, self)._save_m2m(**kwargs)
        self.instance.groups.add(Group.objects.get(name=CreateUserForm.MANAGER))


class CreateMachineForm(CirsFormMixin, forms.ModelForm):
    class Meta:
        model = Machine
        fields = ('name', 'model', 'manufacturer')

    def __init__(self, *args, institution=None, **kwargs):
        super(CreateMachineForm, self).__init__(*args, **kwargs)
        self.institution = institution

    def clean(self):
        cleaned_data = super(CreateMachineForm, self).clean()
        if Machine.objects.filter(institution=self.institution).active().count() >= self.institution.number_of_licenses:
            raise ValidationError("""Your institution already has the maximum number of allowed machine licenses.
                Please contact CIRS support if you believe that this is an error.""")
        return cleaned_data

    def save(self, commit=True):
        self.instance.institution = self.institution
        return super(CreateMachineForm, self).save(commit)


class SequenceForm(CirsFormMixin, forms.ModelForm):
    class Meta:
        model = Sequence
        fields = ('name', 'instructions', 'tolerance')
        widgets = {
            'tolerance': forms.NumberInput(attrs={'step': '0.01'}),
        }

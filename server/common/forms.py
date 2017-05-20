import zipfile

from django import forms

import numpy as np
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import Group
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from process import dicom_import
from .models import Phantom, Institution

UserModel = get_user_model()


class CIRSFormMixin:
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super(CIRSFormMixin, self).__init__(*args, **kwargs)


class AccountForm(CIRSFormMixin, forms.ModelForm):
    class Meta:
        model = UserModel
        fields = ('first_name', 'last_name', 'email')


class CreatePhantomForm(CIRSFormMixin, forms.ModelForm):
    class Meta:
        model = Phantom
        fields = ('name', 'serial_number')

    def clean_serial_number(self):
        try:
            model = Phantom.objects.get(institution=None, serial_number=self.cleaned_data['serial_number']).model
        except ObjectDoesNotExist:
            raise forms.ValidationError("Invalid serial number.")

        self.cleaned_data['model'] = model
        return self.cleaned_data['serial_number']


class UploadScanForm(CIRSFormMixin, forms.Form):
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


class UploadCTForm(CIRSFormMixin, forms.Form):
    dicom_archive = forms.FileField(label="File Browser")

    def clean_dicom_archive(self):
        try:
            dicom_import.combined_series_from_zip(self.cleaned_data['dicom_archive'])
        except dicom_import.DicomImportException as e:
            raise forms.ValidationError(e.args[0])

        with zipfile.ZipFile(self.cleaned_data['dicom_archive'], 'r') as zip_file:
            datasets = dicom_import.dicom_datasets_from_zip(zip_file)

        self.cleaned_data['datasets'] = datasets
        return self.cleaned_data['dicom_archive']


class UploadRawForm(CIRSFormMixin, forms.Form):
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


class InstitutionForm(CIRSFormMixin, forms.ModelForm):
    class Meta:
        model = Institution
        fields = ('name', 'address', 'phone_number')
        labels = {
            'name': "Institution Name",
            'address': "Institution Address",
            'phone_number': "Institution Contact Phone Number",
        }


class DicomOverlayForm(CIRSFormMixin, forms.Form):
    study_instance_uid = forms.CharField(label="StudyInstanceUID", required=False)
    patient_id = forms.CharField(label="PatientID", required=False)
    isocenter_x = forms.FloatField(label="x", widget=forms.NumberInput(attrs={'step': '0.01'}), required=False)
    isocenter_y = forms.FloatField(label="y", widget=forms.NumberInput(attrs={'step': '0.01'}), required=False)
    isocenter_z = forms.FloatField(label="z", widget=forms.NumberInput(attrs={'step': '0.01'}), required=False)
    frame_of_reference_uid = forms.CharField(label="FrameOfReferenceUID", required=False)


class CreateUserForm(CIRSFormMixin, PasswordResetForm):
    MANAGER = 'Manager'
    MEDICAL_PHYSICIST = 'Medical Physicist'
    THERAPIST = 'Therapist'
    GROUP_CHOICES = (
        (MANAGER, 'Admin'),
        (MEDICAL_PHYSICIST, 'Medical Physicist'),
        (THERAPIST, 'Therapist'),
    )

    field_order = ('first_name', 'last_name', 'email', 'user_type')

    first_name = forms.CharField()
    last_name = forms.CharField()
    user_type_ht = """<p>The user type determines what permissions the account will have. Therapist users can upload new MR
            scans for analysis. Medical Physicist users can do everything therapists can do, and can also add and configure
            phantoms, machines, and sequences. Admin users can do everything Medical Physicists can do, and can also add and
            delete new users. Please note that once a user type is set, it cannot be changed (except by CIRS support).</p>"""
    user_type = forms.ChoiceField(choices=GROUP_CHOICES, widget=forms.RadioSelect, help_text=user_type_ht)

    def get_users(self, email):
        active_users = UserModel.objects.filter(**{
            '%s__iexact' % UserModel.get_email_field_name(): email,
            'is_active': True,
        })
        return (u for u in active_users if not u.has_usable_password())

    def save(self, **kwargs):
        user = UserModel(first_name=self.cleaned_data['first_name'],
                         last_name=self.cleaned_data['last_name'],
                         email=self.cleaned_data['email'])
        user.set_unusable_password()
        user.save()
        user.groups.add(Group.objects.get(name=self.cleaned_data['user_type']))
        super(CreateUserForm, self).save(**kwargs)
        return user


class RegisterForm(CIRSFormMixin, CreateUserForm):
    field_order = ('first_name', 'last_name', 'email', 'user_type')

    phantom_serial_number = forms.CharField()
    institution_name = forms.CharField()
    institution_address = forms.CharField()
    institution_phone = forms.CharField(label="Institution Contact Phone Number")
    email_repeat = forms.EmailField()

    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)
        self.fields.pop('user_type')

    def clean(self):
        cleaned_data = super(RegisterForm, self).clean()
        email = cleaned_data['email']
        email_repeat = cleaned_data['email_repeat']

        if email != email_repeat:
            raise ValidationError("Emails do not match.")
        return cleaned_data

    def clean_phantom_serial_number(self):
        serial_number = self.cleaned_data['phantom_serial_number']
        try:
            model = Phantom.objects.get(institution=None, serial_number=serial_number).model
        except ObjectDoesNotExist:
            raise ValidationError("That phantom does not exist in our database. If you believe this is a mistake, "
                                  "please contact CIRS support.")
        available = not Phantom.objects.filter(serial_number=serial_number).exclude(institution=None).exists()
        if not available:
            raise ValidationError("That phantom is already in use by another institution. If you believe this is a "
                                  "mistake, please contact CIRS support.")

        self.cleaned_data['phantom_model'] = model
        return serial_number

import zipfile
from functools import partial

from django import forms

import numpy as np
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import Group
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from process import dicom_import
from .models import Phantom, Institution, User
from .validators import validate_phantom_serial_number


class CIRSFormMixin:
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super(CIRSFormMixin, self).__init__(*args, **kwargs)


class AccountForm(CIRSFormMixin, forms.ModelForm):
    class Meta:
        model = User
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


class CreatePasswordForm(PasswordResetForm):
    def get_users(self, email):
        active_users = User.objects.filter(**{
            '%s__iexact' % User.get_email_field_name(): email,
            'is_active': True,
        })
        return (u for u in active_users if not u.has_usable_password())


class BaseUserForm(CIRSFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs):
        self.create_password_form = None
        super(BaseUserForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(BaseUserForm, self).clean()
        self.create_password_form = CreatePasswordForm({'email': cleaned_data.get('email')})
        if not self.create_password_form.is_valid():
            raise ValidationError("Something went wrong. Please try again, or contact CIRS support"
                                  " if the problem persists.")
        return cleaned_data

    def save(self, commit=True, **kwargs):
        """
        Save this form's self.instance object if commit=True. Otherwise, add
        a save_m2m() method to the form which can be called after the instance
        is saved manually at a later time. Return the model instance.
        """
        if self.errors:
            raise ValueError(
                "The %s could not be %s because the data didn't validate." % (
                    self.instance._meta.object_name,
                    'created' if self.instance._state.adding else 'changed',
                )
            )

        self.instance.set_unusable_password()
        if commit:
            # If committing, save the instance and the m2m data immediately.
            self.instance.save()
            self._save_m2m(**kwargs)
        else:
            # If not committing, add a method to the form to allow deferred
            # saving of m2m data.
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
        (MANAGER, "Admin"),
        (MEDICAL_PHYSICIST, "Medical Physicist"),
        (THERAPIST, "Therapist"),
    )

    field_order = (
        'first_name',
        'last_name',
        'email',
        'user_type',
    )

    user_type_ht = """<p>The user type determines what permissions the account will have. Therapist users can upload new
                MR scans for analysis. Medical Physicist users can do everything therapists can do, and can also add and
                configure phantoms, machines, and sequences. Admin users can do everything Medical Physicists can do,
                and can also add and delete new users. Please note that once a user type is set, it cannot be changed
                (except by CIRS support).</p>"""
    user_type = forms.ChoiceField(choices=GROUP_CHOICES, widget=forms.RadioSelect, help_text=user_type_ht)

    class Meta(BaseUserForm.Meta):
        fields = ('first_name', 'last_name', 'email', 'user_type')

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
        phantom_model = Phantom.objects.get(institution=None,
                                            serial_number=self.cleaned_data['phantom_serial_number']).model
        Phantom.objects.create(serial_number=self.cleaned_data['phantom_serial_number'],
                               model=phantom_model,
                               institution=institution)
        self.instance.institution = institution
        super(RegisterForm, self).save(**kwargs)
        return self.instance

    def _save_m2m(self, **kwargs):
        super(RegisterForm, self)._save_m2m(**kwargs)
        self.instance.groups.add(Group.objects.get(name=CreateUserForm.MANAGER))

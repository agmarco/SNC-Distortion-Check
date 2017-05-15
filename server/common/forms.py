import zipfile

from django import forms

import numpy as np
from django.core.exceptions import ObjectDoesNotExist
from django.utils.safestring import mark_safe

from process import dicom_import
from .models import Phantom, Institution, User

MRI_SOP = '1.2.840.10008.5.1.4.1.1.4'  # MR Image Storage
CT_SOP = '1.2.840.10008.5.1.4.1.1.2'  # CT Image Storage


class CIRSForm(forms.Form):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super().__init__(*args, **kwargs)


class CIRSModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super().__init__(*args, **kwargs)


class AccountForm(CIRSModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')


class CreatePhantomForm(CIRSModelForm):
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


class UploadScanForm(CIRSForm):
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

        #if datasets[0].SOPClassUID != MRI_SOP:
        #    raise forms.ValidationError("The DICOM archive must be of an MRI scan.")

        self.cleaned_data['datasets'] = datasets
        return self.cleaned_data['dicom_archive']


class UploadCTForm(CIRSForm):
    dicom_archive = forms.FileField(label="File Browser")

    def clean_dicom_archive(self):
        try:
            dicom_import.combined_series_from_zip(self.cleaned_data['dicom_archive'])
        except dicom_import.DicomImportException as e:
            raise forms.ValidationError(e.args[0])

        with zipfile.ZipFile(self.cleaned_data['dicom_archive'], 'r') as zip_file:
            datasets = dicom_import.dicom_datasets_from_zip(zip_file)

        #if datasets[0].SOPClassUID != CT_SOP:
        #    raise forms.ValidationError("The DICOM archive must be of a CT scan.")

        self.cleaned_data['datasets'] = datasets
        return self.cleaned_data['dicom_archive']


class UploadRawForm(CIRSForm):
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


class InstitutionForm(CIRSModelForm):
    class Meta:
        model = Institution
        fields = ('name', 'address', 'phone_number')
        labels = {
            'name': "Institution Name",
            'address': "Institution Address",
            'phone_number': "Institution Contact Phone Number",
        }


class DicomOverlayForm(CIRSForm):
    study_instance_uid = forms.CharField(label="StudyInstanceUID", required=False)
    patient_id = forms.CharField(label="PatientID", required=False)
    isocenter_x = forms.FloatField(label="x", widget=forms.NumberInput(attrs={'step': '0.01'}), required=False)
    isocenter_y = forms.FloatField(label="y", widget=forms.NumberInput(attrs={'step': '0.01'}), required=False)
    isocenter_z = forms.FloatField(label="z", widget=forms.NumberInput(attrs={'step': '0.01'}), required=False)
    frame_of_reference_uid = forms.CharField(label="FrameOfReferenceUID", required=False)


class CreateUserForm(CIRSModelForm):
    ADMIN = 'manager'
    MEDICAL_PHYSICIST = 'medical_physicist'
    THERAPIST = 'therapist'
    GROUP_CHOICES = (
        (ADMIN, 'Admin'),
        (MEDICAL_PHYSICIST, 'Medical Physicist'),
        (THERAPIST, 'Therapist'),
    )

    user_type_ht = """The user type determines what permissions the account will have. Therapist users can upload new MR
        scans for analysis. Medical Physicist users can do everyting therapists can do, and can also add and configure
        phantoms, machines, and sequences. Admin users can do everything Medical Physicists can do, and can also add and
        delete new users. Please note that once a user type is set, it cannot be changed (except by CIRS support)."""
    user_type = forms.ChoiceField(choices=GROUP_CHOICES, widget=forms.RadioSelect, help_text=user_type_ht)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'user_type')

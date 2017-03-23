import zipfile

import numpy as np

from django import forms
from django.core.files.base import ContentFile

from process import dicom_import
from process.feature_detection import FeatureDetector

from .models import Phantom, GoldenFiducials
from .factories import DicomSeriesFactory, FiducialsFactory, GoldenFiducialsFactory


class UploadScanForm(forms.Form):
    dicom_archive = forms.FileField()

    def clean_dicom_archive(self):
        try:
            dicom_import.combined_series_from_zip(self.cleaned_data['dicom_archive'])
        except dicom_import.DicomImportException as e:
            raise forms.ValidationError(e.args[0])

        return self.cleaned_data


class UploadCTForm(forms.ModelForm):
    dicom_archive = forms.FileField(label="File browser")

    class Meta:
        model = Phantom
        fields = ()

    def clean_dicom_archive(self):
        try:
            dicom_import.combined_series_from_zip(self.cleaned_data['dicom_archive'])
        except dicom_import.DicomImportException as e:
            raise forms.ValidationError(e.args[0])

        return self.cleaned_data


class UploadRawForm(forms.ModelForm):
    csv = forms.FileField(label="File browser")

    class Meta:
        model = Phantom
        fields = ()

    def clean_csv(self):
        return self.cleaned_data

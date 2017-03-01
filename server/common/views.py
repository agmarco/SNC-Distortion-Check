import logging

from django.shortcuts import render
from django.http import HttpResponse
from django.urls import reverse
from django import forms

from server.common.models import Scan
import dicom_import 


logger = logging.getLogger(__name__)


class UploadScanForm(forms.Form):
    dicom_archive = forms.FileField()

    def clean_dicom_archive(self):
        try:
            dicom_import.combined_series_from_zip(self.cleaned_data['dicom_archive'])
        except dicom_import.DicomImportException as e:
            raise forms.ValidationError(e.args[0])

        return self.cleaned_data


def upload_file(request):
    if request.method == 'POST':
        form_with_data = UploadScanForm(request.POST, request.FILES)
        if form_with_data.is_valid():
            instance = Scan(dicom_archive=request.FILES['dicom_archive'])
            logger.info("Starting to save")
            instance.save()
            logger.info("Done saving")

            message = 'Upload was successful'
            form = UploadScanForm()
        else:
            message = 'Error uploading'
            form = form_with_data
    else:
        message = ''
        form = UploadScanForm()

    return render(request, 'scan_upload.html', {'form': form, 'message': message})

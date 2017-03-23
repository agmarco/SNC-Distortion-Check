from django import forms

from process import dicom_import


class UploadScanForm(forms.Form):
    dicom_archive = forms.FileField()

    def clean_dicom_archive(self):
        try:
            dicom_import.combined_series_from_zip(self.cleaned_data['dicom_archive'])
        except dicom_import.DicomImportException as e:
            raise forms.ValidationError(e.args[0])

        return self.cleaned_data


class UploadCTForm(forms.Form):
    dicom_archive = forms.FileField(label="File browser")

    def clean_dicom_archive(self):
        try:
            dicom_import.combined_series_from_zip(self.cleaned_data['dicom_archive'])
        except dicom_import.DicomImportException as e:
            raise forms.ValidationError(e.args[0])

        return self.cleaned_data


class UploadRawForm(forms.Form):
    csv = forms.FileField(label="File browser")

    def clean_csv(self):
        return self.cleaned_data
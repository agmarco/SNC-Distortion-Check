import zipfile

from django import forms

from process import dicom_import


class UploadScanForm(forms.Form):
    dicom_archive = forms.FileField(label="File browser")

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
            with zipfile.ZipFile(self.cleaned_data['dicom_archive'], 'r') as zip_file:
                datasets = dicom_import.dicom_datasets_from_zip(zip_file)
        except dicom_import.DicomImportException as e:
            raise forms.ValidationError(e.args[0])

        if datasets[0].Modality != 'CT':
            raise forms.ValidationError("The DICOM archive must be of modality 'CT.'")

        return self.cleaned_data


class UploadRawForm(forms.Form):
    csv = forms.FileField(label="File browser")

    def clean_csv(self):
        return self.cleaned_data

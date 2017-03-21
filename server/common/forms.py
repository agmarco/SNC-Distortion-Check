from django import forms
from process import dicom_import

from .models import Phantom, Machine, Sequence


class UploadScanForm(forms.Form):
    dicom_archive = forms.FileField()

    def clean_dicom_archive(self):
        try:
            dicom_import.combined_series_from_zip(self.cleaned_data['dicom_archive'])
        except dicom_import.DicomImportException as e:
            raise forms.ValidationError(e.args[0])

        return self.cleaned_data


class AddPhantomForm(forms.ModelForm):
    class Meta:
        model = Phantom
        fields = ('name', 'model', 'serial_number')


class EditPhantomForm(forms.ModelForm):
    class Meta:
        model = Phantom
        fields = ('name',)


class MachineForm(forms.ModelForm):
    class Meta:
        model = Machine
        fields = ('name', 'model', 'manufacturer')


class SequenceForm(forms.ModelForm):
    class Meta:
        model = Sequence
        fields = ('name', 'instructions')

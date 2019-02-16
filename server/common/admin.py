from django.contrib import admin, messages

from .http import ZipResponse
from . import models


@admin.register(models.Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('name', 'license_expiration_date', 'scans_remaining')
    actions = ('set_active',)

    def set_active(self, request, queryset):
        if queryset.count() > 1:
            self.message_user(request, "You may only set one institution to active.", level=messages.WARNING)
        elif queryset.count() == 1:
            request.session['institution'] = queryset[0].pk
        else:
            request.sessoin['institution'] = None
    set_active.short_description = "Set selected institution as active"


@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
    exclude = ('user_permissions', 'password')
    list_display = ('first_name', 'last_name', 'email', 'institution')


class PurchaseOrderInline(admin.TabularInline):
    model = models.PurchaseOrder
    fields = 'number',


@admin.register(models.Phantom)
class PhantomAdmin(admin.ModelAdmin):
    list_display = ('name', 'institution', 'model', 'serial_number')
    inlines = PurchaseOrderInline,


@admin.register(models.PhantomModel)
class PhantomModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'model_number')


@admin.register(models.Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ('name', 'institution', 'model', 'manufacturer')


@admin.register(models.Sequence)
class SequenceAdmin(admin.ModelAdmin):
    list_display = ('name', 'institution', 'instructions')


@admin.register(models.MachineSequencePair)
class MachineSequencePairAdmin(admin.ModelAdmin):
    pass


@admin.register(models.DicomSeries)
class DicomSeriesAdmin(admin.ModelAdmin):
    list_display = ('zipped_dicom_files', 'modality', 'acquisition_date', 'rows', 'columns',
            'number_of_slices', 'series_uid', 'patient_id')


@admin.register(models.Scan)
class ScanAdmin(admin.ModelAdmin):
    list_display = (
        'creator',
        'pk',
        'created_on',
        'passed',
        'processing',
        'tolerance',
        'errors',
        'notes',
    )
    exclude = ('dicom_series', 'detected_fiducials', 'golden_fiducials', 'TP_A_S', 'TP_B')
    actions = ('download_dicom',)
    ordering = ('-created_on',)

    def download_dicom(self, request, queryset):
        if queryset.count() > 1:
            self.message_user(request, "You may only download DICOM files for 1 scan at a time.", level=messages.WARNING)
        else:
            dicom_series = queryset[0].dicom_series
            if dicom_series is None:
                self.message_user(request, "The selected scan has no DICOM files.", level=messages.WARNING)
            else:
                dicom_archive = dicom_series.zipped_dicom_files
                return ZipResponse(dicom_archive.file, dicom_archive.file.name.split('/')[-1])
    download_dicom.short_description = "Download DICOM files for selected scan"

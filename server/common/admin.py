from django.contrib import admin
from . import models


@admin.register(models.Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('name', 'number_of_licenses')

@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
    exclude = ('user_permissions',)
    list_display = ('first_name', 'last_name', 'email', 'institution')

@admin.register(models.Phantom)
class PhantomAdmin(admin.ModelAdmin):
    list_display = ('name', 'institution', 'model', 'serial_number')

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
    readonly_fields = ('series_uid',)

@admin.register(models.Fiducials)
class FiducialsAdmin(admin.ModelAdmin):
    pass

@admin.register(models.GoldenFiducials)
class GoldenFiducialsAdmin(admin.ModelAdmin):
    pass

@admin.register(models.Scan)
class ScanAdmin(admin.ModelAdmin):
    pass

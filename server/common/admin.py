from django.contrib import admin

from . import models


def set_active(modeladmin, request, queryset):
    if len(queryset) > 1:
        raise ValueError("You may only set one institution to active.")
    request.session['institution'] = queryset[0].pk
set_active.short_description = "Set selected institution as active"


@admin.register(models.Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('name', 'number_of_licenses')
    actions = [set_active]


@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
    exclude = ('user_permissions',)
    list_display = ('first_name', 'last_name', 'email', 'institution')


@admin.register(models.Phantom)
class PhantomAdmin(admin.ModelAdmin):
    list_display = ('name', 'institution', 'model', 'serial_number')


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
    readonly_fields = ('series_uid',)


@admin.register(models.Fiducials)
class FiducialsAdmin(admin.ModelAdmin):
    list_display = ('created_on',)


@admin.register(models.GoldenFiducials)
class GoldenFiducialsAdmin(admin.ModelAdmin):
    list_display = ('type', 'processing', 'phantom', 'created_on')


@admin.register(models.Scan)
class ScanAdmin(admin.ModelAdmin):
    pass

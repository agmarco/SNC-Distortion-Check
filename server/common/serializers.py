from django.urls import reverse

from rest_framework import serializers

from .models import MachineSequencePair, Machine, Sequence, Phantom, Scan, Institution, GoldenFiducials


class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = ('pk', 'name', 'number_of_licenses', 'address', 'phone_number')


class MachineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Machine
        fields = ('pk', 'name', 'model', 'manufacturer')


class SequenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sequence
        fields = ('pk', 'name', 'instructions')


class MachineSequencePairSerializer(serializers.ModelSerializer):
    machine = MachineSerializer()
    sequence = SequenceSerializer()
    latest_scan_date = serializers.ReadOnlyField()
    latest_scan_passed = serializers.ReadOnlyField()
    detail_url = serializers.SerializerMethodField()

    class Meta:
        model = MachineSequencePair
        fields = (
            'pk',
            'machine',
            'sequence',
            'latest_scan_date',
            'latest_scan_passed',
            'detail_url',
            'tolerance',
        )

    def get_detail_url(self, pair):
        return reverse('machine_sequence_detail', args=(pair.pk,))

        
class PhantomSerializer(serializers.ModelSerializer):
    model_number = serializers.SerializerMethodField()
    gold_standard_grid_locations = serializers.SerializerMethodField()
    upload_raw_url = serializers.SerializerMethodField()
    upload_ct_url = serializers.SerializerMethodField()

    class Meta:
        model = Phantom
        fields = (
            'pk',
            'name',
            'model_number',
            'serial_number',
            'gold_standard_grid_locations',
            'upload_raw_url',
            'upload_ct_url',
        )

    def get_model_number(self, phantom):
        return phantom.model.model_number

    def get_gold_standard_grid_locations(self, phantom):
        return phantom.active_gold_standard.source_summary

    def get_upload_raw_url(self, golden_fiducials):
        return reverse('upload_raw', args=(golden_fiducials.phantom.pk,))

    def get_upload_ct_url(self, golden_fiducials):
        return reverse('upload_ct', args=(golden_fiducials.phantom.pk,))


class ScanSerializer(serializers.ModelSerializer):
    phantom = PhantomSerializer()
    passed = serializers.ReadOnlyField()
    acquisition_date = serializers.ReadOnlyField()
    errors_url = serializers.SerializerMethodField()
    delete_url = serializers.SerializerMethodField()
    dicom_overlay_url = serializers.SerializerMethodField()
    raw_data_url = serializers.SerializerMethodField()
    refresh_url = serializers.SerializerMethodField()
    full_report_url = serializers.SerializerMethodField()
    executive_report_url = serializers.SerializerMethodField()
    error_mags = serializers.ReadOnlyField()

    class Meta:
        model = Scan
        fields = (
            'pk',
            'phantom',
            'processing',
            'errors',
            'passed',
            'acquisition_date',
            'errors_url',
            'delete_url',
            'dicom_overlay_url',
            'raw_data_url',
            'refresh_url',
            'full_report_url',
            'executive_report_url',
            'error_mags',
        )

    def get_errors_url(self, scan):
        return reverse('scan_errors', args=(scan.pk,))

    def get_delete_url(self, scan):
        return reverse('delete_scan', args=(scan.pk,))

    def get_dicom_overlay_url(self, scan):
        return reverse('dicom_overlay', args=(scan.pk,))

    def get_raw_data_url(self, scan):
        return scan.raw_data.name and scan.raw_data.url

    def get_refresh_url(self, scan):
        return reverse('refresh_scan', args=(scan.pk,))

    def get_full_report_url(self, scan):
        return scan.full_report.name and scan.full_report.url

    def get_executive_report_url(self, scan):
        return scan.executive_report.name and scan.executive_report.url


class GoldenFiducialsSerializer(serializers.ModelSerializer):
    dicom_series_filename = serializers.SerializerMethodField()
    zipped_dicom_files_url = serializers.SerializerMethodField()
    csv_url = serializers.SerializerMethodField()
    activate_url = serializers.SerializerMethodField()
    delete_url = serializers.SerializerMethodField()

    class Meta:
        model = GoldenFiducials
        fields = (
            'pk',
            'is_active',
            'created_on',
            'type',
            'processing',
            'dicom_series_filename',
            'zipped_dicom_files_url',
            'csv_url',
            'activate_url',
            'delete_url',
        )

    def get_dicom_series_filename(self, golden_fiducials):
        if golden_fiducials.dicom_series is None:
            return None
        else:
            return golden_fiducials.dicom_series.filename

    def get_zipped_dicom_files_url(self, golden_fiducials):
        if golden_fiducials.dicom_series is None:
            return None
        else:
            return golden_fiducials.dicom_series.zipped_dicom_files.url

    def get_csv_url(self, golden_fiducials):
        return reverse('gold_standard_csv', args=(golden_fiducials.phantom.pk, golden_fiducials.pk))

    def get_activate_url(self, golden_fiducials):
        return reverse('activate_gold_standard', args=(golden_fiducials.phantom.pk, golden_fiducials.pk))

    def get_delete_url(self, golden_fiducials):
        return reverse('delete_gold_standard', args=(golden_fiducials.phantom.pk, golden_fiducials.pk))

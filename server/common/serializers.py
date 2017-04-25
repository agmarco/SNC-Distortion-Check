from django.urls import reverse

import numpy as np
from rest_framework import serializers

from .models import MachineSequencePair, Machine, Sequence, Phantom, Scan


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

    class Meta:
        model = Phantom
        fields = ('pk', 'name', 'model_number', 'serial_number', 'gold_standard_grid_locations')

    def get_model_number(self, phantom):
        return phantom.model.model_number

    def get_gold_standard_grid_locations(self, phantom):
        return phantom.active_gold_standard.source_summary


class ScanSerializer(serializers.ModelSerializer):
    phantom = PhantomSerializer()
    passed = serializers.ReadOnlyField()
    acquisition_date = serializers.SerializerMethodField()
    errors_url = serializers.SerializerMethodField()
    delete_url = serializers.SerializerMethodField()
    zipped_dicom_files_url = serializers.SerializerMethodField()
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
            'zipped_dicom_files_url',
            'full_report_url',
            'executive_report_url',
            'error_mags',
        )

    def get_acquisition_date(self, scan):
        return scan.dicom_series.acquisition_date

    def get_errors_url(self, scan):
        return reverse('scan_errors', args=(scan.pk,))

    def get_delete_url(self, scan):
        return reverse('delete_scan', args=(scan.pk,))

    def get_zipped_dicom_files_url(self, scan):
        return scan.dicom_series.zipped_dicom_files.url

    def get_full_report_url(self, scan):
        return scan.full_report.name and scan.full_report.url

    def get_executive_report_url(self, scan):
        return scan.executive_report.name and scan.executive_report.url

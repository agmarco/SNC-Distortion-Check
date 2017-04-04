from django.urls import reverse
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
    latest_scan_within_tolerance = serializers.ReadOnlyField()
    detail_url = serializers.SerializerMethodField()

    class Meta:
        model = MachineSequencePair
        fields = (
            'pk',
            'machine',
            'sequence',
            'latest_scan_date',
            'latest_scan_within_tolerance',
            'detail_url',
        )

    def get_detail_url(self, obj):
        return reverse('machine_sequence_detail', args=(obj.pk,))

        
class PhantomSerializer(serializers.ModelSerializer):
    model_number = serializers.SerializerMethodField()
    gold_standard_grid_locations = serializers.SerializerMethodField()

    class Meta:
        model = Phantom
        fields = ('pk', 'name', 'model_number', 'serial_number', 'gold_standard_grid_locations')

    def get_model_number(self, obj):
        return obj.model.model_number

    def get_gold_standard_grid_locations(self, obj):
        return obj.active_gold_standard.source_summary


class ScanSerializer(serializers.ModelSerializer):
    acquisition_date = serializers.SerializerMethodField()
    phantom = PhantomSerializer()

    class Meta:
        model = Scan
        fields = ('pk', 'acquisition_date', 'phantom', 'processing', 'errors')

    def get_acquisition_date(self, obj):
        return obj.dicom_series.acquisition_date

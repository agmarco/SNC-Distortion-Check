from rest_framework import serializers

from .models import MachineSequencePair, Machine, Sequence


class MachineSequencePairSerializer(serializers.ModelSerializer):
    latest_scan_date = serializers.Field()
    latest_scan_within_tolerance = serializers.Field()

    class Meta:
        model = MachineSequencePair
        fields = (
            'pk',
            'machine',
            'sequence',
            'latest_scan_date',
            'latest_scan_within_tolerance',
        )


class MachineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Machine
        fields = ('pk', 'name',)


class SequenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sequence
        fields = ('pk', 'name',)

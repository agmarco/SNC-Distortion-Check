from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .models import MachineSequencePair, Phantom, Scan
from .permissions import login_and_permission_required, validate_institution
from .validators import validate_phantom_serial_number
from .serializers import ScanSerializer


class ValidateSerialView(APIView):
    def post(self, request):
        serial_number = request.data['serial_number']

        try:
            validate_phantom_serial_number(serial_number)
        except ValidationError as err:
            return Response({'valid': False, 'model_number': None, 'message': err})
        else:
            phantom = Phantom.objects.get(serial_number=serial_number)
            return Response({'valid': True, 'model_number': phantom.model.model_number, 'message': None})


class UpdateToleranceView(APIView):
    permission_classes = (
        login_and_permission_required('common.configuration'),
        validate_institution(model_class=MachineSequencePair),
    )

    def post(self, request):
        machine_sequence_pair = get_object_or_404(MachineSequencePair, pk=request.data['pk'])
        machine_sequence_pair.tolerance = request.data['tolerance']
        machine_sequence_pair.save()
        return Response()


class PollScansView(APIView):
    permission_classes = (
        IsAuthenticated,
        # validate_institution(model_class=MachineSequencePair),  # TODO handle lists
    )

    def get(self, request):
        scans = Scan.objects.filter(pk__in=request.data['scan_pks'], processing=False)
        serializer = ScanSerializer(scans, many=True)
        return Response(serializer.data)

from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404

from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Phantom, MachineSequencePair
from .permissions import login_and_permission_required, validate_institution


class ValidateSerialView(APIView):
    def post(self, request):
        serial_number = request.data['serial_number']
        try:
            phantom = Phantom.objects.get(institution=None, serial_number=serial_number)
        except ObjectDoesNotExist:
            return Response({'exists': False, 'available': False, 'model_number': None})
        available = not Phantom.objects.filter(serial_number=serial_number).exclude(institution=None).exists()
        return Response({'exists': True, 'available': available, 'model_number': phantom.model.model_number})


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

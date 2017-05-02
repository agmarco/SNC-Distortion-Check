from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404

from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Phantom, MachineSequencePair
from .permissions import login_and_permission_required, validate_institution


class ValidateSerial(APIView):
    permission_classes = (login_and_permission_required('common.configuration'),)

    def post(self, request):
        try:
            phantom = Phantom.objects.get(institution=None, serial_number=request.data['serial_number'])
        except ObjectDoesNotExist:
            return Response({'valid': False, 'model_number': None})
        return Response({'valid': True, 'model_number': phantom.model.model_number})


class UpdateTolerance(APIView):
    permission_classes = (
        login_and_permission_required('common.configuration'),
        validate_institution(model_class=MachineSequencePair),
    )

    def post(self, request):
        machine_sequence_pair = get_object_or_404(MachineSequencePair, pk=request.data['pk'])
        machine_sequence_pair.tolerance = request.data['tolerance']
        machine_sequence_pair.save()
        return Response()

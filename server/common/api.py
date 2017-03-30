from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework.views import APIView

from .decorators import login_and_permission_required
from .models import Phantom


# TODO don't use the decorator here
@login_and_permission_required('common.configuration')
class ValidateSerial(APIView):
    def post(self, request):
        try:
            phantom = Phantom.objects.get(institution=None, serial_number=request.data['serial_number'])
        except ObjectDoesNotExist:
            return Response({'valid': False, 'model_number': None})
        return Response({'valid': True, 'model_number': phantom.model.model_number})

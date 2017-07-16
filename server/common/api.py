import os, json, boto3
import uuid

from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .models import MachineSequencePair, Phantom, Scan, GoldenFiducials
from .permissions import login_and_permission_required, validate_institution
from .validators import validate_phantom_serial_number
from .serializers import ScanSerializer, GoldenFiducialsSerializer


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
        validate_institution(model_class=MachineSequencePair, pk_url_kwarg='machine_sequence_pair_pk'),
    )

    def post(self, request):
        scans = Scan.objects.filter(
            machine_sequence_pair=request.data['machine_sequence_pair_pk'],
            pk__in=request.data['scan_pks'],
            processing=False,
        )
        serializer = ScanSerializer(scans, many=True)
        return Response(serializer.data)


class PollCtView(APIView):
    permission_classes = (
        IsAuthenticated,
        validate_institution(model_class=Phantom, pk_url_kwarg='phantom_pk'),
    )

    def post(self, request):
        golden_fiducials_set = GoldenFiducials.objects.filter(
            phantom=request.data['phantom_pk'],
            pk__in=request.data['golden_fiducials_pks'],
            processing=False,
        )
        serializer = GoldenFiducialsSerializer(golden_fiducials_set, many=True)
        return Response(serializer.data)


class SignS3View(APIView):
    permission_classes = (
        IsAuthenticated,
    )

    def post(self, request):
        S3_BUCKET = os.environ.get('S3_BUCKET')

        file_name = request.POST.get('file_name')
        file_name = f"{uuid.uuid4()}.{file_name.split('.')[-1]}"
        file_type = request.POST.get('file_type')

        s3 = boto3.client('s3')

        presigned_post = s3.generate_presigned_post(
            Bucket=S3_BUCKET,
            Key=file_name,
            Fields={"acl": "public-read", "Content-Type": file_type},
            Conditions=[
                {"acl": "public-read"},
                {"Content-Type": file_type}
            ],
            ExpiresIn=3600
        )

        return json.dumps({
            'data': presigned_post,
            'url': 'https://%s.s3.amazonaws.com/%s' % (S3_BUCKET, file_name)
        })

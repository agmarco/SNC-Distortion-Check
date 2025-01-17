import os
import boto3
import uuid

from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.conf import settings

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .models import MachineSequencePair, Phantom, Scan, GoldenFiducials
from .permissions import login_and_permission_required, validate_institution, check_license
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
        check_license(),
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
        check_license(),
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
        check_license(),
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
        check_license(check_scans=True),
    )

    def get(self, request):
        S3_BUCKET = os.environ.get('AWS_STORAGE_BUCKET_NAME')

        file_name, ext = os.path.splitext(request.GET.get('file_name'))
        file_path = os.path.join('dicom_series/zipped_dicom_files', f'{uuid.uuid4()}{ext}')
        file_type = request.GET.get('file_type')

        if settings.DEBUG or settings.TESTING:
            base_url = 'http://localhost'
            dev_port = '8000'
            api_endpoint = '/api/upload-as-dev/'
            return Response({
                'data': {
                    'fields': {
                        'file_name': file_name,
                        'file_path': file_path,
                        'ok': True,
                    },
                    'url': f'{base_url}:{dev_port}{api_endpoint}',
                },
                'url': f'{file_path}',  # In dev env, this url is used to locate the file
            })

        else:
            s3 = boto3.client('s3')

            presigned_post = s3.generate_presigned_post(
                Bucket=S3_BUCKET,
                Key=file_path,
                Fields={"Content-Type": file_type},
                Conditions=[
                    {"Content-Type": file_type}
                ],
                ExpiresIn=3600
            )

            return Response({
                'data': presigned_post,
                'url': os.path.join(f'https://{S3_BUCKET}.s3.amazonaws.com', file_path),
            })


class UploadAsDev(APIView):
    def post(self, request, format=None):
        if settings.DEBUG or settings.TESTING:
            full_path = '/'.join([settings.MEDIA_ROOT, request.POST.get('file_path')])
            uploaded_file = request.FILES.get('file')
            with open(full_path, 'wb+') as f:
                for chunk in uploaded_file.chunks():
                    f.write(chunk)
            return Response()
        else:
            return Response(status=403)

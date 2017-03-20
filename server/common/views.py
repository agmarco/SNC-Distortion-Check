import logging

from django.shortcuts import render

from .models import Scan
from .tasks import process_scan
from .forms import UploadScanForm

logger = logging.getLogger(__name__)


def upload_file(request):
    if request.method == 'POST':
        form_with_data = UploadScanForm(request.POST, request.FILES)
        if form_with_data.is_valid():
            scan = Scan(dicom_archive=request.FILES['dicom_archive'])
            logger.info("Starting to save")
            scan.processing = True
            scan.save()
            logger.info("Done saving")
            process_scan.delay(scan.pk)

            message = 'Upload was successful'
            form = UploadScanForm()
        else:
            message = 'Error uploading'
            form = form_with_data
    else:
        message = 'Upload a Scan!'
        form = UploadScanForm()

    scans = Scan.objects.all()

    return render(request, 'scan_upload.html', {
        'form': form,
        'message': message,
        'scans': scans,
    })


def configuration(request):
    institution = request.user.institution

    return render(request, 'configuration.html', {
        'phantoms': institution.phantom_set.objects.all(),
        'machines': institution.machine_set.objects.all(),
        'sequences': institution.sequence_set.objects.all(),
        'users': institution.user_set.objects.all(),
    })

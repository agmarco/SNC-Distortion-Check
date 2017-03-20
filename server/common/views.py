import logging

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect

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


@login_required
def configuration(request):
    if not request.user.groups.filter(name='medical_physicists').count():
        raise PermissionDenied

    institution = request.user.institution
    return render(request, 'configuration.html', {
        'phantoms': institution.phantom_set.filter(deleted=False),
        'machines': institution.machine_set.filter(deleted=False),
        'sequences': institution.sequence_set.filter(deleted=False),
        'users': institution.user_set.filter(deleted=False),
    })


def add_phantom(request):
    return render(request, 'add_phantom.html')


def edit_phantom(request):
    return render(request, 'edit_phantom.html')


def delete_phantom(request):
    return redirect('configuration')


def add_machine(request):
    return render(request, 'add_machine.html')


def edit_machine(request):
    return render(request, 'edit_machine.html')


def delete_machine(request):
    return redirect('configuration')


def add_sequence(request):
    return render(request, 'add_sequence.html')


def edit_sequence(request):
    return render(request, 'edit_sequence.html')


def delete_sequence(request):
    return redirect('configuration')


def add_user(request):
    return render(request, 'add_user.html')


def edit_user(request):
    return render(request, 'edit_user.html')


def delete_user(request):
    return redirect('configuration')

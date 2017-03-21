import logging

from django.contrib.auth.decorators import login_required, permission_required
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
@permission_required('common.configuration', raise_exception=True)
def configuration(request):
    institution = request.user.institution
    return render(request, 'configuration.html', {
        'phantoms': institution.phantom_set.filter(deleted=False),
        'machines': institution.machine_set.filter(deleted=False),
        'sequences': institution.sequence_set.filter(deleted=False),
        'users': institution.user_set.filter(deleted=False),
    })


@login_required
@permission_required('common.configuration', raise_exception=True)
def add_phantom(request):
    return render(request, 'add_phantom.html')


@login_required
@permission_required('common.configuration', raise_exception=True)
def edit_phantom(request, pk):
    return render(request, 'edit_phantom.html')


@login_required
@permission_required('common.configuration', raise_exception=True)
def delete_phantom(request, pk):
    return redirect('configuration')


@login_required
@permission_required('common.configuration', raise_exception=True)
def add_machine(request):
    return render(request, 'add_machine.html')


@login_required
@permission_required('common.configuration', raise_exception=True)
def edit_machine(request, pk):
    return render(request, 'edit_machine.html')


@login_required
@permission_required('common.configuration', raise_exception=True)
def delete_machine(request, pk):
    return redirect('configuration')


@login_required
@permission_required('common.configuration', raise_exception=True)
def add_sequence(request):
    return render(request, 'add_sequence.html')


@login_required
@permission_required('common.configuration', raise_exception=True)
def edit_sequence(request, pk):
    return render(request, 'edit_sequence.html')


@login_required
@permission_required('common.configuration', raise_exception=True)
def delete_sequence(request, pk):
    return redirect('configuration')


@login_required
@permission_required('common.configuration', raise_exception=True)
def add_user(request):
    return render(request, 'add_user.html')


@login_required
@permission_required('common.configuration', raise_exception=True)
def edit_user(request, pk):
    return render(request, 'edit_user.html')


@login_required
@permission_required('common.configuration', raise_exception=True)
def delete_user(request, pk):
    return redirect('configuration')

import logging
import zipfile

import numpy as np

from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile
from django.urls import reverse
from django.views.generic.edit import CreateView, UpdateView, DeleteView, ModelFormMixin, FormView
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy

from process import dicom_import
from process.feature_detection import FeatureDetector
from server.common.factories import DicomSeriesFactory, FiducialsFactory, GoldenFiducialsFactory
from .models import Scan, Phantom, Machine, Sequence, GoldenFiducials
from .tasks import process_scan
from .forms import UploadScanForm, UploadCTForm, UploadRawForm
from .decorators import validate_institution, login_and_permission_required
from .mixins import DeletionMixin

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

    return render(request, 'common/scan_upload.html', {
        'form': form,
        'message': message,
        'scans': scans,
    })


@login_and_permission_required('common.configuration')
def configuration(request):
    institution = request.user.institution
    return render(request, 'common/configuration.html', {
        'phantoms': institution.phantom_set.active(),
        'machines': institution.machine_set.active(),
        'sequences': institution.sequence_set.active(),
        'users': institution.user_set.active(),
    })


@login_and_permission_required('common.configuration')
class CreatePhantom(CreateView):
    model = Phantom
    fields = ('name', 'model', 'serial_number')
    success_url = reverse_lazy('configuration')
    template_name_suffix = '_create'

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.institution = self.request.user.institution
        self.object.save()
        return super(ModelFormMixin, self).form_valid(form)


@login_and_permission_required('common.configuration')
@validate_institution()
class UpdatePhantom(UpdateView):
    model = Phantom
    fields = ('name',)
    success_url = reverse_lazy('configuration')
    template_name_suffix = '_update'


@login_and_permission_required('common.configuration')
@validate_institution()
class DeletePhantom(DeletionMixin, DeleteView):
    model = Phantom
    success_url = reverse_lazy('configuration')


@login_and_permission_required('common.configuration')
class CreateMachine(CreateView):
    model = Machine
    fields = ('name', 'model', 'manufacturer')
    success_url = reverse_lazy('configuration')
    template_name_suffix = '_create'

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.institution = self.request.user.institution
        self.object.save()
        return super(ModelFormMixin, self).form_valid(form)


@login_and_permission_required('common.configuration')
@validate_institution()
class UpdateMachine(UpdateView):
    model = Machine
    fields = ('name', 'model', 'manufacturer')
    success_url = reverse_lazy('configuration')
    template_name_suffix = '_update'


@login_and_permission_required('common.configuration')
@validate_institution()
class DeleteMachine(DeletionMixin, DeleteView):
    model = Machine
    success_url = reverse_lazy('configuration')


@login_and_permission_required('common.configuration')
class CreateSequence(CreateView):
    model = Sequence
    fields = ('name', 'instructions')
    success_url = reverse_lazy('configuration')
    template_name_suffix = '_create'

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.institution = self.request.user.institution
        self.object.save()
        return super(ModelFormMixin, self).form_valid(form)


@login_and_permission_required('common.configuration')
@validate_institution()
class UpdateSequence(UpdateView):
    model = Sequence
    fields = ('name', 'instructions')
    success_url = reverse_lazy('configuration')
    template_name_suffix = '_update'


@login_and_permission_required('common.configuration')
@validate_institution()
class DeleteSequence(DeletionMixin, DeleteView):
    model = Sequence
    success_url = reverse_lazy('configuration')


@login_and_permission_required('common.configuration')
class GoldenFiducialsCTUpload(FormView):
    form_class = UploadCTForm
    template_name = 'common/upload_ct.html'

    def form_valid(self, form):
        # create DICOM series
        with zipfile.ZipFile(self.request.FILES['dicom_archive'], 'r') as zip_file:
            datasets = dicom_import.dicom_datasets_from_zip(zip_file)

        voxels, ijk_to_xyz = dicom_import.combine_slices(datasets)
        dicom_series = DicomSeriesFactory(
            voxels=voxels,
            ijk_to_xyz=ijk_to_xyz,
            shape=voxels.shape,
            series_uid=datasets[0].SeriesInstanceUID,
        )
        content_file = ContentFile(b'')
        np.save(content_file, voxels)
        dicom_series.zipped_dicom_files.save(name='voxels', content=content_file)

        # create fiducials
        modality = datasets[0].Modality
        points_in_patient_xyz = FeatureDetector(form.instance.name, modality, voxels, ijk_to_xyz).run()

        fiducials = FiducialsFactory(fiducials=points_in_patient_xyz)

        logger.info(points_in_patient_xyz)

        # create golden fiducials
        GoldenFiducialsFactory(
            phantom=form.instance,
            is_active=False,
            dicom_series=dicom_series,
            fiducials=fiducials,
            type=GoldenFiducials.CT,
        )
        return super(GoldenFiducialsCTUpload, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(GoldenFiducialsCTUpload, self).get_context_data(**kwargs)
        context.update({'pk': self.kwargs['pk']})
        return context

    def get_success_url(self):
        return reverse('update_phantom', args=(self.kwargs['pk'],))


@login_and_permission_required('common.configuration')
class GoldenFiducialsRawUpload(FormView):
    form_class = UploadRawForm
    template_name = 'common/upload_raw.html'

    def get_context_data(self, **kwargs):
        context = super(GoldenFiducialsRawUpload, self).get_context_data(**kwargs)
        context.update({'pk': self.kwargs['pk']})
        return context

    def get_success_url(self):
        return reverse('update_phantom', args=(self.kwargs['pk'],))


@login_and_permission_required('common.configuration')
@validate_institution(get_institution=lambda obj: obj.phantom.institution)
class DeleteGoldenFiducials(DeletionMixin, DeleteView):
    model = GoldenFiducials

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.type == GoldenFiducials.CAD or self.object.is_active:
            raise PermissionDenied
        return super(DeleteGoldenFiducials, self).delete(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('update_phantom', args=(self.kwargs['phantom_pk'],))

    def get_context_data(self, **kwargs):
        context = super(DeleteGoldenFiducials, self).get_context_data(**kwargs)
        context.update({'phantom_pk': self.kwargs['phantom_pk']})
        return context


@login_and_permission_required('common.configuration')
@validate_institution(model_class=GoldenFiducials, get_institution=lambda obj: obj.phantom.institution)
def activate_golden_fiducials(request, phantom_pk=None, pk=None):
    golden_fiducials = get_object_or_404(GoldenFiducials, pk=pk)
    golden_fiducials.activate()
    return redirect('update_phantom', phantom_pk)


@login_and_permission_required('common.configuration')
def create_user(request):
    return render(request, 'common/user_create.html')


@login_and_permission_required('common.configuration')
def update_user(request, pk=None):
    return render(request, 'common/user_update.html')


@login_and_permission_required('common.configuration')
def delete_user(request, pk=None):
    return redirect('configuration')

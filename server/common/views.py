import csv
import logging
import zipfile

from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic.edit import CreateView, UpdateView, DeleteView, ModelFormMixin, FormView
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy

import numpy as np

from process import dicom_import
from server.common.factories import DicomSeriesFactory, FiducialsFactory, GoldenFiducialsFactory
from .models import Scan, Phantom, Machine, Sequence, GoldenFiducials, User
from .tasks import process_scan, process_ct_upload
from .forms import UploadScanForm, UploadCTForm, UploadRawForm
from .decorators import validate_institution, login_and_permission_required

logger = logging.getLogger(__name__)


class CirsDeleteView(DeleteView):
    """A view providing the ability to delete objects by setting their 'deleted' attribute."""

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.deleted = True
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


@login_and_permission_required('common.configuration')
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
    manage_users = request.user.has_perm('common.manage_users')
    return render(request, 'common/configuration.html', {
        'phantoms': institution.phantom_set.active().order_by('-last_modified_on'),
        'machines': institution.machine_set.active().order_by('-last_modified_on'),
        'sequences': institution.sequence_set.active().order_by('-last_modified_on'),
        'users': institution.user_set.active().order_by('-last_modified_on') if manage_users else [],
        'manage_users': manage_users,
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
    pk_url_kwarg = 'phantom_pk'

    @property
    def golden_fiducials(self):
        return self.object.goldenfiducials_set.active().order_by('-last_modified_on')


@login_and_permission_required('common.configuration')
@validate_institution()
class DeletePhantom(CirsDeleteView):
    model = Phantom
    success_url = reverse_lazy('configuration')
    pk_url_kwarg = 'phantom_pk'


@login_and_permission_required('common.configuration')
@validate_institution(model_class=Phantom, pk_url_kwarg='phantom_pk')
class UploadCT(FormView):
    form_class = UploadCTForm
    template_name = 'common/upload_ct.html'

    def form_valid(self, form):
        with zipfile.ZipFile(self.request.FILES['dicom_archive'], 'r') as zip_file:
            datasets = dicom_import.dicom_datasets_from_zip(zip_file)
        voxels, ijk_to_xyz = dicom_import.combine_slices(datasets)

        dicom_series = DicomSeriesFactory(
            zipped_dicom_files=self.request.FILES['dicom_archive'],
            voxels=voxels,
            ijk_to_xyz=ijk_to_xyz,
            shape=voxels.shape,
            datasets=datasets,
        )
        process_ct_upload.delay(self.kwargs['phantom_pk'], dicom_series.pk)

        return super(UploadCT, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(UploadCT, self).get_context_data(**kwargs)
        context.update({'phantom_pk': self.kwargs['phantom_pk']})
        return context

    def get_success_url(self):
        return reverse('update_phantom', args=(self.kwargs['phantom_pk'],))


@login_and_permission_required('common.configuration')
@validate_institution(model_class=Phantom, pk_url_kwarg='phantom_pk')
class UploadRaw(FormView):
    form_class = UploadRawForm
    template_name = 'common/upload_raw.html'

    def form_valid(self, form):
        phantom = Phantom.objects.get(pk=self.kwargs['phantom_pk'])
        fiducials = FiducialsFactory(fiducials=np.genfromtxt(self.request.FILES['csv'], delimiter=',').T)
        GoldenFiducialsFactory(
            phantom=phantom,
            fiducials=fiducials,
            type=GoldenFiducials.RAW,
        )
        return super(UploadRaw, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(UploadRaw, self).get_context_data(**kwargs)
        context.update({'phantom_pk': self.kwargs['phantom_pk']})
        return context

    def get_success_url(self):
        return reverse('update_phantom', args=(self.kwargs['phantom_pk'],))


@login_and_permission_required('common.configuration')
@validate_institution()
class DeleteGoldStandard(CirsDeleteView):
    model = GoldenFiducials
    pk_url_kwarg = 'gold_standard_pk'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.type == GoldenFiducials.CAD or self.object.is_active:
            raise PermissionDenied
        return super(DeleteGoldStandard, self).delete(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('update_phantom', args=(self.kwargs['phantom_pk'],))

    def get_context_data(self, **kwargs):
        context = super(DeleteGoldStandard, self).get_context_data(**kwargs)
        context.update({'phantom_pk': self.kwargs['phantom_pk']})
        return context


@login_and_permission_required('common.configuration')
@validate_institution(model_class=GoldenFiducials, pk_url_kwarg='gold_standard_pk')
def activate_gold_standard(request, phantom_pk=None, gold_standard_pk=None):
    golden_fiducials = get_object_or_404(GoldenFiducials, pk=gold_standard_pk)
    golden_fiducials.activate()
    return redirect('update_phantom', phantom_pk)


@login_and_permission_required('common.configuration')
@validate_institution(model_class=GoldenFiducials, pk_url_kwarg='gold_standard_pk')
def gold_standard_csv(request, phantom_pk=None, gold_standard_pk=None):
    golden_fiducials = get_object_or_404(GoldenFiducials, pk=gold_standard_pk)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{golden_fiducials.source_summary}.csv"'

    writer = csv.writer(response)
    for fiducial in golden_fiducials.fiducials.fiducials.T:
        writer.writerow(fiducial)
    return response


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
class DeleteMachine(CirsDeleteView):
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
class DeleteSequence(CirsDeleteView):
    model = Sequence
    success_url = reverse_lazy('configuration')


@login_and_permission_required('common.manage_users')
class CreateUser(CreateView):
    model = User
    fields = ('username', 'first_name', 'last_name', 'email')
    success_url = reverse_lazy('configuration')
    template_name_suffix = '_create'

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.institution = self.request.user.institution
        self.object.save()
        return super(ModelFormMixin, self).form_valid(form)


@login_and_permission_required('common.manage_users')
@validate_institution()
class UpdateUser(UpdateView):
    model = User
    fields = ('username', 'first_name', 'last_name', 'email')
    success_url = reverse_lazy('configuration')
    template_name_suffix = '_update'


@login_and_permission_required('common.manage_users')
@validate_institution()
class DeleteUser(CirsDeleteView):
    model = User
    success_url = reverse_lazy('configuration')

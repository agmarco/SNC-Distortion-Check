import csv
import logging
import zipfile

from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic.edit import CreateView, UpdateView, DeleteView, ModelFormMixin, FormView
from django.shortcuts import render, redirect, get_object_or_404

import numpy as np

from process import dicom_import
from server.common.factories import DicomSeriesFactory, FiducialsFactory, GoldenFiducialsFactory
from .models import Scan, Phantom, Machine, Sequence, GoldenFiducials, User, Institution
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
class Configuration(UpdateView):
    model = Institution
    fields = ('name', 'address', 'phone_number')
    template_name = 'common/configuration.html'

    def _get_message(self):
        action = self.request.GET.get('action')
        message = None

        if action:
            if action == 'update_institution_success':
                message = f"\"{self.get_object().name}\" has been updated successfully."
            elif action == 'create_phantom_success':
                phantom = Phantom.objects.get(pk=self.request.GET.get('pk'))
                message = f"\"{phantom.name}\" has been created successfully."
            elif action == 'update_phantom_success':
                phantom = Phantom.objects.get(pk=self.request.GET.get('pk'))
                message = f"\"{phantom.name}\" has been updated successfully."
            elif action == 'delete_phantom_success':
                phantom = Phantom.objects.get(pk=self.request.GET.get('pk'))
                message = f"\"{phantom.name}\" has been deleted successfully."
            elif action == 'create_machine_success':
                machine = Machine.objects.get(pk=self.request.GET.get('pk'))
                message = f"\"{machine.name}\" has been created successfully."
            elif action == 'update_machine_success':
                machine = Machine.objects.get(pk=self.request.GET.get('pk'))
                message = f"\"{machine.name}\" has been updated successfully."
            elif action == 'delete_machine_success':
                machine = Machine.objects.get(pk=self.request.GET.get('pk'))
                message = f"\"{machine.name}\" has been deleted successfully."
            elif action == 'create_sequence_success':
                sequence = Sequence.objects.get(pk=self.request.GET.get('pk'))
                message = f"\"{sequence.name}\" has been created successfully."
            elif action == 'update_sequence_success':
                sequence = Sequence.objects.get(pk=self.request.GET.get('pk'))
                message = f"\"{sequence.name}\" has been updated successfully."
            elif action == 'delete_sequence_success':
                sequence = Sequence.objects.get(pk=self.request.GET.get('pk'))
                message = f"\"{sequence.name}\" has been deleted successfully."
            elif action == 'create_user_success':
                user = User.objects.get(pk=self.request.GET.get('pk'))
                message = f"\"{user.get_full_name()}\" has been created successfully."
            elif action == 'delete_user_success':
                user = User.objects.get(pk=self.request.GET.get('pk'))
                message = f"\"{user.get_full_name()}\" has been deleted successfully."
        return message

    def get_object(self, queryset=None):
        return self.request.user.institution

    def get_success_url(self):
        return f"{reverse('configuration')}?action=update_institution_success"

    def get_context_data(self, **kwargs):
        context = super(Configuration, self).get_context_data(**kwargs)
        institution = self.get_object()
        manage_users = self.request.user.has_perm('common.manage_users')
        context.update({
            'phantoms': institution.phantom_set.active().order_by('-last_modified_on'),
            'machines': institution.machine_set.active().order_by('-last_modified_on'),
            'sequences': institution.sequence_set.active().order_by('-last_modified_on'),
            'users': institution.user_set.active().order_by('-last_modified_on') if manage_users else [],
            'manage_users': manage_users,
            'message': self._get_message(),
        })
        return context


@login_and_permission_required('common.configuration')
class CreatePhantom(CreateView):
    model = Phantom
    fields = ('name', 'model', 'serial_number')
    template_name_suffix = '_create'

    def get_success_url(self):
        return f"{reverse('configuration')}?action=create_phantom_success&pk={self.object.pk}"

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
    template_name_suffix = '_update'
    pk_url_kwarg = 'phantom_pk'

    def _get_message(self):
        action = self.request.GET.get('action')
        message = None

        if action:
            if action == 'upload_ct_success':
                message = "Gold Standard CT has been uploaded successfully. When it is finished processing, it will appear below."
            elif action == 'upload_raw_success':
                message = "Gold Standard Points have been uploaded successfully."
            elif action == 'delete_gold_standard_success':
                gold_standard = GoldenFiducials.objects.get(pk=self.request.GET.get('pk'))
                message = f"\"{gold_standard.source_summary}\" has been deleted successfully."
            elif action == 'activate_gold_standard_success':
                gold_standard = GoldenFiducials.objects.get(pk=self.request.GET.get('pk'))
                message = f"\"{gold_standard.source_summary}\" has been activated successfully."
        return message

    def get_success_url(self):
        return f"{reverse('configuration')}?action=update_phantom_success&pk={self.object.pk}"

    def get_context_data(self, **kwargs):
        context = super(UpdatePhantom, self).get_context_data(**kwargs)
        context.update({
            'message': self._get_message(),
        })
        return context

    @property
    def golden_fiducials(self):
        return self.object.goldenfiducials_set.active().order_by('-last_modified_on')


@login_and_permission_required('common.configuration')
@validate_institution()
class DeletePhantom(CirsDeleteView):
    model = Phantom
    pk_url_kwarg = 'phantom_pk'

    def get_success_url(self):
        return f"{reverse('configuration')}?action=delete_phantom_success&pk={self.object.pk}"


@login_and_permission_required('common.configuration')
class CreateMachine(CreateView):
    model = Machine
    fields = ('name', 'model', 'manufacturer')
    template_name_suffix = '_create'

    def get_success_url(self):
        return f"{reverse('configuration')}?action=create_machine_success&pk={self.object.pk}"

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
    template_name_suffix = '_update'

    def get_success_url(self):
        return f"{reverse('configuration')}?action=update_machine_success&pk={self.object.pk}"


@login_and_permission_required('common.configuration')
@validate_institution()
class DeleteMachine(CirsDeleteView):
    model = Machine

    def get_success_url(self):
        return f"{reverse('configuration')}?action=delete_machine_success&pk={self.object.pk}"


@login_and_permission_required('common.configuration')
class CreateSequence(CreateView):
    model = Sequence
    fields = ('name', 'instructions')
    template_name_suffix = '_create'

    def get_success_url(self):
        return f"{reverse('configuration')}?action=create_sequence_success&pk={self.object.pk}"

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
    template_name_suffix = '_update'

    def get_success_url(self):
        return f"{reverse('configuration')}?action=update_sequence_success&pk={self.object.pk}"


@login_and_permission_required('common.configuration')
@validate_institution()
class DeleteSequence(CirsDeleteView):
    model = Sequence

    def get_success_url(self):
        return f"{reverse('configuration')}?action=delete_sequence_success&pk={self.object.pk}"


@login_and_permission_required('common.manage_users')
class CreateUser(CreateView):
    model = User
    fields = ('username', 'first_name', 'last_name', 'email')
    template_name_suffix = '_create'

    def get_success_url(self):
        return f"{reverse('configuration')}?action=create_user_success&pk={self.object.pk}"

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.institution = self.request.user.institution
        self.object.save()
        return super(ModelFormMixin, self).form_valid(form)


@login_and_permission_required('common.manage_users')
@validate_institution()
class DeleteUser(CirsDeleteView):
    model = User

    def get_success_url(self):
        return f"{reverse('configuration')}?action=delete_user_success&pk={self.object.pk}"


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
        return f"{reverse('update_phantom', args=(self.kwargs['phantom_pk'],))}?action=upload_ct_success"


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

    def get_success_url(self):
        return f"{reverse('update_phantom', args=(self.kwargs['phantom_pk'],))}?action=upload_raw_success"

    def get_context_data(self, **kwargs):
        context = super(UploadRaw, self).get_context_data(**kwargs)
        context.update({'phantom_pk': self.kwargs['phantom_pk']})
        return context


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
        return f"{reverse('update_phantom', args=(self.kwargs['phantom_pk'],))}?action=delete_gold_standard_success&pk={self.object.pk}"

    def get_context_data(self, **kwargs):
        context = super(DeleteGoldStandard, self).get_context_data(**kwargs)
        context.update({'phantom_pk': self.kwargs['phantom_pk']})
        return context


@login_and_permission_required('common.configuration')
@validate_institution(model_class=GoldenFiducials, pk_url_kwarg='gold_standard_pk')
def activate_gold_standard(request, phantom_pk=None, gold_standard_pk=None):
    golden_fiducials = get_object_or_404(GoldenFiducials, pk=gold_standard_pk)
    golden_fiducials.activate()
    return redirect(f"{reverse('update_phantom', args=(phantom_pk,))}?action=activate_gold_standard_success&pk={gold_standard_pk}")


@login_and_permission_required('common.configuration')
@validate_institution(model_class=GoldenFiducials, pk_url_kwarg='gold_standard_pk')
def gold_standard_csv(request, phantom_pk=None, gold_standard_pk=None):
    golden_fiducials = get_object_or_404(GoldenFiducials, pk=gold_standard_pk)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{golden_fiducials.source_summary}.csv"'

    writer = csv.writer(response)
    for row in golden_fiducials.fiducials.fiducials.T:
        writer.writerow(row)
    return response

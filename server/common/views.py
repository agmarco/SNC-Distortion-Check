import csv
import logging
from datetime import datetime

from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, ModelFormMixin, FormView
from django.shortcuts import render, redirect, get_object_or_404
from rest_framework.renderers import JSONRenderer

from process import dicom_import
from .models import Scan, Phantom, Machine, Sequence, Fiducials, GoldenFiducials, User, DicomSeries, Institution, MachineSequencePair
from .tasks import process_scan, process_ct_upload
from .forms import UploadScanForm, UploadCTForm, UploadRawForm
from .serializers import MachineSequencePairSerializer, MachineSerializer, SequenceSerializer
from .decorators import validate_institution, login_and_permission_required

logger = logging.getLogger(__name__)


class CSVResponse(HttpResponse):
    def __init__(self, ndarray, filename=None, *args, **kwargs):
        kwargs.setdefault('content_type', 'text/csv')
        super(CSVResponse, self).__init__(*args, **kwargs)

        self['Content-Disposition'] = f'attachment; filename="{filename or "array.csv"}"'
        writer = csv.writer(self)
        for row in ndarray.T:
            writer.writerow(row)


class CirsDeleteView(DeleteView):
    """A view providing the ability to delete objects by setting their 'deleted' attribute."""

    def __init__(self, **kwargs):
        self.object = None
        super(CirsDeleteView, self).__init__(**kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.deleted = True
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


@login_and_permission_required('common.configuration')
def upload_scan(request):
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
    success_url = reverse_lazy('configuration')
    template_name = 'common/configuration.html'

    def get_object(self, queryset=None):
        return self.request.user.institution

    def form_valid(self, form):
        messages.success(self.request, f"\"{self.object.name}\" has been updated successfully.")
        return super(Configuration, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(Configuration, self).get_context_data(**kwargs)
        institution = self.get_object()
        context.update({
            'phantoms': institution.phantom_set.active().order_by('-last_modified_on'),
            'machines': institution.machine_set.active().order_by('-last_modified_on'),
            'sequences': institution.sequence_set.active().order_by('-last_modified_on'),
        })
        if self.request.user.has_perm('common.manage_users'):
            context['users'] = institution.user_set.active().order_by('-last_modified_on')
        return context


@login_and_permission_required('common.configuration')
def landing(request):
    machine_sequence_pairs_queryset = MachineSequencePair.objects.filter(machine__institution=request.user.institution)
    machine_sequence_pairs = MachineSequencePairSerializer(machine_sequence_pairs_queryset, many=True)
    machines = MachineSerializer(Machine.objects.filter(institution=request.user.institution), many=True)
    sequences = SequenceSerializer(Sequence.objects.filter(institution=request.user.institution), many=True)

    renderer = JSONRenderer()
    return render(request, 'common/landing.html', {
        'machine_sequence_pairs': renderer.render(machine_sequence_pairs.data),
        'machines': renderer.render(machines.data),
        'sequences': renderer.render(sequences.data),
    })


@login_and_permission_required('common.configuration')
def machine_sequences(request):
    machine_sequence_pairs_queryset = MachineSequencePair.objects.filter(machine__institution=request.user.institution)
    machine_sequence_pairs = MachineSequencePairSerializer(machine_sequence_pairs_queryset, many=True)
    machines = MachineSerializer(Machine.objects.filter(institution=request.user.institution), many=True)
    sequences = SequenceSerializer(Sequence.objects.filter(institution=request.user.institution), many=True)

    renderer = JSONRenderer()
    return render(request, 'common/machine_sequences.html', {
        'machine_sequence_pairs': renderer.render(machine_sequence_pairs.data),
        'machines': renderer.render(machines.data),
        'sequences': renderer.render(sequences.data),
    })


@login_and_permission_required('common.configuration')
@validate_institution()
class MachineSequenceDetail(DetailView):
    model = MachineSequencePair

    def get_context_data(self, **kwargs):
        machine_sequence_pair = MachineSequencePairSerializer(self.object)

        renderer = JSONRenderer()
        return {
            'machine_sequence_pair': renderer.render(machine_sequence_pair.data),
        }


# TODO check the serial number again
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
        messages.success(self.request, f"\"{self.object.name}\" has been created successfully.")
        return super(ModelFormMixin, self).form_valid(form)


@login_and_permission_required('common.configuration')
@validate_institution()
class UpdatePhantom(UpdateView):
    model = Phantom
    fields = ('name',)
    success_url = reverse_lazy('configuration')
    template_name_suffix = '_update'
    pk_url_kwarg = 'phantom_pk'

    def form_valid(self, form):
        messages.success(self.request, f"\"{self.object.name}\" has been updated successfully.")
        return super(UpdatePhantom, self).form_valid(form)

    @property
    def golden_fiducials(self):
        return self.object.goldenfiducials_set.active().order_by('-last_modified_on')


@login_and_permission_required('common.configuration')
@validate_institution()
class DeletePhantom(CirsDeleteView):
    model = Phantom
    success_url = reverse_lazy('configuration')
    pk_url_kwarg = 'phantom_pk'

    def delete(self, request, *args, **kwargs):
        response = super(DeletePhantom, self).delete(request, *args, **kwargs)
        messages.success(self.request, f"\"{self.object.name}\" has been deleted successfully.")
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
        messages.success(self.request, f"\"{self.object.name}\" has been created successfully.")
        return super(ModelFormMixin, self).form_valid(form)


@login_and_permission_required('common.configuration')
@validate_institution()
class UpdateMachine(UpdateView):
    model = Machine
    fields = ('name', 'model', 'manufacturer')
    success_url = reverse_lazy('configuration')
    template_name_suffix = '_update'

    def form_valid(self, form):
        messages.success(self.request, f"\"{self.object.name}\" has been updated successfully.")
        return super(UpdateMachine, self).form_valid(form)


@login_and_permission_required('common.configuration')
@validate_institution()
class DeleteMachine(CirsDeleteView):
    model = Machine
    success_url = reverse_lazy('configuration')

    def delete(self, request, *args, **kwargs):
        response = super(DeleteMachine, self).delete(request, *args, **kwargs)
        messages.success(self.request, f"\"{self.object.name}\" has been deleted successfully.")
        return response


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
        messages.success(self.request, f"\"{self.object.name}\" has been created successfully.")
        return super(ModelFormMixin, self).form_valid(form)


@login_and_permission_required('common.configuration')
@validate_institution()
class UpdateSequence(UpdateView):
    model = Sequence
    fields = ('name', 'instructions')
    success_url = reverse_lazy('configuration')
    template_name_suffix = '_update'

    def form_valid(self, form):
        messages.success(self.request, f"\"{self.object.name}\" has been updated successfully.")
        return super(UpdateSequence, self).form_valid(form)


@login_and_permission_required('common.configuration')
@validate_institution()
class DeleteSequence(CirsDeleteView):
    model = Sequence
    success_url = reverse_lazy('configuration')

    def delete(self, request, *args, **kwargs):
        response = super(DeleteSequence, self).delete(request, *args, **kwargs)
        messages.success(self.request, f"\"{self.object.name}\" has been deleted successfully.")
        return response


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
        messages.success(self.request, f"\"{self.object.get_full_name()}\" has been created successfully.")
        return super(ModelFormMixin, self).form_valid(form)


@login_and_permission_required('common.manage_users')
@validate_institution()
class DeleteUser(CirsDeleteView):
    model = User
    success_url = reverse_lazy('configuration')

    def delete(self, request, *args, **kwargs):
        response = super(DeleteUser, self).delete(request, *args, **kwargs)
        messages.success(self.request, f"\"{self.object.get_full_name()}\" has been deleted successfully.")
        return response


@login_and_permission_required('common.configuration')
@validate_institution(model_class=Phantom, pk_url_kwarg='phantom_pk')
class UploadCT(FormView):
    form_class = UploadCTForm
    template_name = 'common/upload_ct.html'

    def form_valid(self, form):
        voxels, ijk_to_xyz = dicom_import.combine_slices(form.cleaned_data['datasets'])

        dicom_series = DicomSeries.objects.create(
            zipped_dicom_files=self.request.FILES['dicom_archive'],
            voxels=voxels,
            ijk_to_xyz=ijk_to_xyz,
            shape=voxels.shape,
            series_uid=form.cleaned_data['datasets'][0].SeriesInstanceUID,
            acquisition_date=datetime.strptime(form.cleaned_data['datasets'][0].AcquisitionDate, '%Y%m%d'),
        )

        gold_standard = GoldenFiducials.objects.create(
            phantom=Phantom.objects.get(pk=self.kwargs['phantom_pk']),
            dicom_series=dicom_series,
            type=GoldenFiducials.CT,
            processing=True,
        )

        process_ct_upload.delay(dicom_series.pk, gold_standard.pk)
        messages.success(self.request, "Your gold standard CT has been uploaded successfully.")
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
        fiducials = Fiducials.objects.create(fiducials=form.cleaned_data['fiducials'])
        GoldenFiducials.objects.create(
            phantom=phantom,
            fiducials=fiducials,
            type=GoldenFiducials.CSV,
        )
        messages.success(self.request, "Your gold standard points have been uploaded successfully.")
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
        messages.success(self.request, f"\"{self.object.source_summary}\" has been deleted successfully.")
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
    gold_standard = get_object_or_404(GoldenFiducials, pk=gold_standard_pk)
    gold_standard.activate()
    messages.success(request, f"\"{gold_standard.source_summary}\" has been activated successfully.")
    return redirect('update_phantom', phantom_pk)


@login_and_permission_required('common.configuration')
@validate_institution(model_class=GoldenFiducials, pk_url_kwarg='gold_standard_pk')
def gold_standard_csv(request, phantom_pk=None, gold_standard_pk=None):
    gold_standard = get_object_or_404(GoldenFiducials, pk=gold_standard_pk)
    return CSVResponse(gold_standard.fiducials.fiducials, filename=f'{gold_standard.source_summary}.csv')

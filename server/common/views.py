import csv
import logging
from datetime import datetime

from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils import formats
from django.utils.functional import cached_property
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, ModelFormMixin, FormView
from django.shortcuts import render, redirect, get_object_or_404
from rest_framework.renderers import JSONRenderer

from process import dicom_import
from .models import Scan, Phantom, Machine, Sequence, Fiducials, GoldenFiducials, User, DicomSeries, Institution, MachineSequencePair
from .tasks import process_scan, process_ct_upload
from .forms import UploadScanForm, UploadCTForm, UploadRawForm, CreatePhantomForm, InstitutionForm, DicomOverlayForm
from .serializers import MachineSequencePairSerializer, MachineSerializer, SequenceSerializer, PhantomSerializer, ScanSerializer
from .decorators import validate_institution, login_and_permission_required

logger = logging.getLogger(__name__)


class CSVResponse(HttpResponse):
    def __init__(self, ndarray, filename="array.csv", *args, **kwargs):
        kwargs.setdefault('content_type', 'text/csv')
        super(CSVResponse, self).__init__(*args, **kwargs)

        self['Content-Disposition'] = f'attachment; filename="{filename}"'
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
def landing(request):
    machine_sequence_pairs_queryset = MachineSequencePair.objects.filter(machine__institution=request.user.institution)
    machine_sequence_pairs_queryset = machine_sequence_pairs_queryset.active().order_by('-last_modified_on')
    machine_sequence_pairs = MachineSequencePairSerializer(machine_sequence_pairs_queryset, many=True)

    renderer = JSONRenderer()
    return render(request, 'common/landing.html', {
        'machine_sequence_pairs': renderer.render(machine_sequence_pairs.data),
    })


@login_and_permission_required('common.configuration')
class Configuration(UpdateView):
    model = Institution
    form_class = InstitutionForm
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


# TODO scan table ordering is backwards when the acquisition dates are the same
@login_and_permission_required('common.configuration')
@validate_institution()
class MachineSequenceDetail(DetailView):
    model = MachineSequencePair
    template_name = 'common/machine_sequence_detail.html'

    def get_context_data(self, **kwargs):
        machine_sequence_pair = MachineSequencePairSerializer(self.object)
        scans = ScanSerializer(Scan.objects.filter(machine_sequence_pair=self.object).active().order_by('-dicom_series__acquisition_date'), many=True)

        renderer = JSONRenderer()
        return {
            'machine_sequence_pair': renderer.render(machine_sequence_pair.data),
            'scans': renderer.render(scans.data)
        }


# TODO handle prepopulated machine and sequence
# TODO cancel might take the user back to landing, machine-sequences, or machine-sequence-detail
@login_and_permission_required('common.configuration')
class UploadScan(FormView):
    form_class = UploadScanForm
    template_name = 'common/upload_scan.html'

    def get_context_data(self, **kwargs):
        institution = self.request.user.institution
        machines = MachineSerializer(Machine.objects.filter(institution=institution), many=True)
        sequences = SequenceSerializer(Sequence.objects.filter(institution=institution), many=True)
        phantoms = PhantomSerializer(Phantom.objects.filter(institution=institution), many=True)

        renderer = JSONRenderer()
        return {
            'machines': renderer.render(machines.data),
            'sequences': renderer.render(sequences.data),
            'phantoms': renderer.render(phantoms.data),
        }

    def form_valid(self, form):
        machine = Machine.objects.get(pk=form.cleaned_data['machine'])
        sequence = Sequence.objects.get(pk=form.cleaned_data['sequence'])
        phantom = Phantom.objects.get(pk=form.cleaned_data['phantom'])

        try:
            machine_sequence_pair = MachineSequencePair.objects.get(machine=machine, sequence=sequence)
        except ObjectDoesNotExist:
            machine_sequence_pair = MachineSequencePair.objects.create(machine=machine, sequence=sequence, tolerance=3)

        dicom_datasets = form.cleaned_data['datasets']
        voxels, ijk_to_xyz = dicom_import.combine_slices(dicom_datasets)
        dicom_series = DicomSeries.objects.create(
            zipped_dicom_files=self.request.FILES['dicom_archive'],
            voxels=voxels,
            ijk_to_xyz=ijk_to_xyz,
            shape=voxels.shape,
            series_uid=dicom_datasets[0].SeriesInstanceUID,
            acquisition_date=datetime.strptime(dicom_datasets[0].AcquisitionDate, '%Y%m%d'),
        )

        scan = Scan.objects.create(
            creator=self.request.user,
            machine_sequence_pair=machine_sequence_pair,
            dicom_series=dicom_series,
            golden_fiducials=phantom.active_gold_standard,
            notes=form.cleaned_data['notes'],
            tolerance=machine_sequence_pair.tolerance,
            processing=True,
        )

        process_scan.delay(scan.pk)
        messages.success(self.request, "Your scan has been uploaded successfully and is processing.")
        return redirect('machine_sequence_detail', machine_sequence_pair.pk)

    def form_invalid(self, form):
        renderer = JSONRenderer()
        context = self.get_context_data(form=form)
        context.update({'form_errors': renderer.render(form.errors)})
        return self.render_to_response(context)


@login_and_permission_required('common.configuration')
@validate_institution()
class ScanErrors(DetailView):
    model = Scan
    template_name = 'common/scan_errors.html'


@login_and_permission_required('common.configuration')
@validate_institution(model_class=Scan)
class DicomOverlay(FormView):
    form_class = DicomOverlayForm
    template_name = 'common/dicom_overlay.html'

    @cached_property
    def scan(self):
        return get_object_or_404(Scan, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super(DicomOverlay, self).get_context_data(**kwargs)
        context.update({'scan': self.scan})
        return context

    def get_success_url(self):
        return reverse('machine_sequence_detail', args=(self.scan.machine_sequence_pair.pk,))

    def form_valid(self, form):
        messages.success(self.request, f"""
        DICOM overlay for scan for phantom \"{self.scan.golden_fiducials.phantom.model.model_number} —
        {self.scan.golden_fiducials.phantom.serial_number},\"
        captured on {formats.date_format(self.scan.dicom_series.acquisition_date)}, has been generated successfully.
        """)
        # TODO generate overlay
        return super(DicomOverlay, self).form_valid(form)


@login_and_permission_required('common.configuration')
@validate_institution()
class DeleteScan(CirsDeleteView):
    model = Scan

    def delete(self, request, *args, **kwargs):
        response = super(DeleteScan, self).delete(request, *args, **kwargs)
        messages.success(self.request, f"""Scan for phantom
            \"{self.object.golden_fiducials.phantom.model.model_number} —
            {self.object.golden_fiducials.phantom.serial_number}\", captured on
            {formats.date_format(self.object.dicom_series.acquisition_date)}, has been deleted successfully."""
        )
        return response

    def get_success_url(self):
        return reverse('machine_sequence_detail', args=(self.object.machine_sequence_pair.pk,))


@login_and_permission_required('common.configuration')
class CreatePhantom(FormView):
    form_class = CreatePhantomForm
    success_url = reverse_lazy('configuration')
    template_name = 'common/phantom_create.html'

    def __init__(self, **kwargs):
        self.object = None
        super(CreatePhantom, self).__init__(**kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.institution = self.request.user.institution
        self.object.model = form.cleaned_data['model']
        self.object.save()
        messages.success(self.request, f"\"{self.object.name}\" has been created successfully.")
        return super(CreatePhantom, self).form_valid(form)

    def form_invalid(self, form):
        renderer = JSONRenderer()
        context = self.get_context_data(form=form)
        context.update({'form_errors': renderer.render(form.errors)})
        return self.render_to_response(context)


@login_and_permission_required('common.configuration')
@validate_institution()
class UpdatePhantom(UpdateView):
    model = Phantom
    fields = ('name',)
    template_name_suffix = '_update'
    pk_url_kwarg = 'phantom_pk'

    def form_valid(self, form):
        messages.success(self.request, f"\"{self.object.name}\" has been updated successfully.")
        return super(UpdatePhantom, self).form_valid(form)

    def get_success_url(self):
        return reverse('update_phantom', args=(self.kwargs['phantom_pk'],))

    @property
    def golden_fiducials(self):
        return self.object.goldenfiducials_set.active().order_by('-created_on')


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
        messages.success(self.request, "Your gold standard CT has been uploaded successfully and is processing.")
        return super(UploadCT, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(UploadCT, self).get_context_data(**kwargs)
        phantom = get_object_or_404(Phantom, pk=self.kwargs['phantom_pk'])
        context.update({'phantom': phantom})
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
        phantom = get_object_or_404(Phantom, pk=self.kwargs['phantom_pk'])
        context.update({'phantom': phantom})
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
        else:
            messages.success(self.request, f"\"{self.object.source_summary}\" has been deleted successfully.")
            return super(DeleteGoldStandard, self).delete(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('update_phantom', args=(self.kwargs['phantom_pk'],))

    def get_context_data(self, **kwargs):
        context = super(DeleteGoldStandard, self).get_context_data(**kwargs)
        phantom = get_object_or_404(Phantom, pk=self.kwargs['phantom_pk'])
        context.update({'phantom': phantom})
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

import os
import io
import tempfile
import zipfile
import logging
import time
from datetime import datetime

import dicom
from dicom.UID import generate_uid
from dicom.dataset import Dataset, FileDataset
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordResetConfirmView, PasswordResetCompleteView, PasswordResetDoneView
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponseNotAllowed
from django.urls import reverse, reverse_lazy
from django.utils import formats
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, ModelFormMixin, FormView
from django.shortcuts import render, redirect, get_object_or_404
from rest_framework.renderers import JSONRenderer

import scipy.io
import numpy as np
import scipy.ndimage.filters
from scipy.interpolate.ndgriddata import griddata

from process import dicom_import
from process.affine import apply_affine
from . import models
from . import serializers
from . import forms
from .tasks import process_scan, process_ct_upload
from .decorators import validate_institution, login_and_permission_required
from .http import CSVResponse, ZipResponse

logger = logging.getLogger(__name__)


class JsonFormMixin:
    renderer = JSONRenderer()
    form_class = None

    def get_context_data(self, **kwargs):
        context = super(JsonFormMixin, self).get_context_data(**kwargs)
        context.update({
            'form_initial': self.renderer.render({name: '' for name in self.form_class.base_fields.keys()}),
        })
        return context

    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        context.update({
            'form_data': self.renderer.render({name: form[name].data for name in self.form_class.base_fields.keys()}),
            'form_errors': self.renderer.render(form.errors),
        })
        return self.render_to_response(context)


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


@login_required
def landing_view(request):
    machine_sequence_pairs_queryset = models.MachineSequencePair.objects.filter(machine__institution=request.user.institution)
    machine_sequence_pairs_queryset = machine_sequence_pairs_queryset.active().order_by('-last_modified_on')
    machine_sequence_pairs_json = serializers.MachineSequencePairSerializer(machine_sequence_pairs_queryset, many=True)

    renderer = JSONRenderer()
    return render(request, 'common/landing.html', {
        'machine_sequence_pairs_json': renderer.render(machine_sequence_pairs_json.data),
    })


@login_and_permission_required('common.configuration')
class ConfigurationView(UpdateView):
    model = models.Institution
    form_class = forms.InstitutionForm
    success_url = reverse_lazy('configuration')
    template_name = 'common/configuration.html'

    def get_object(self, queryset=None):
        return self.request.user.institution

    def form_valid(self, form):
        messages.success(self.request, f"\"{self.object.name}\" has been updated successfully.")
        return super(ConfigurationView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(ConfigurationView, self).get_context_data(**kwargs)
        institution = self.get_object()
        context.update({
            'phantoms': institution.phantom_set.active().order_by('-last_modified_on'),
            'machines': institution.machine_set.active().order_by('-last_modified_on'),
            'sequences': institution.sequence_set.active().order_by('-last_modified_on'),
        })
        if self.request.user.has_perm('common.manage_users'):
            context['users'] = institution.user_set.active().order_by('-last_modified_on')
        return context


@method_decorator(login_required, name='dispatch')
class AccountView(UpdateView):
    model = models.User
    form_class = forms.AccountForm
    success_url = reverse_lazy('account')
    template_name = 'common/account.html'

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Your account has been updated successfully.")
        return super(AccountView, self).form_valid(form)


@method_decorator(login_required, name='dispatch')
@validate_institution()
class MachineSequenceDetailView(DetailView):
    model = models.MachineSequencePair
    template_name = 'common/machine_sequence_detail.html'

    def get_context_data(self, **kwargs):
        machine_sequence_pair_json = serializers.MachineSequencePairSerializer(self.object)
        scans_json = models.Scan.objects.filter(machine_sequence_pair=self.object)
        scans_json = scans_json.active().order_by('-dicom_series__acquisition_date', '-created_on')
        scans_json = serializers.ScanSerializer(scans_json, many=True)

        renderer = JSONRenderer()
        return {
            'machine_sequence_pair': self.object,
            'machine_sequence_pair_json': renderer.render(machine_sequence_pair_json.data),
            'scans_json': renderer.render(scans_json.data)
        }


# TODO cancel might take the user back to landing, machine-sequences, or machine-sequence-detail
@method_decorator(login_required, name='dispatch')
class UploadScanView(JsonFormMixin, FormView):
    form_class = forms.UploadScanForm
    template_name = 'common/upload_scan.html'
    renderer = JSONRenderer()

    def get_context_data(self, **kwargs):
        institution = self.request.user.institution
        machines_json = serializers.MachineSerializer(models.Machine.objects.filter(institution=institution), many=True)
        sequences_json = serializers.SequenceSerializer(models.Sequence.objects.filter(institution=institution), many=True)
        phantoms_json = serializers.PhantomSerializer(models.Phantom.objects.filter(institution=institution), many=True)

        return {
            'machines_json': self.renderer.render(machines_json.data),
            'sequences_json': self.renderer.render(sequences_json.data),
            'phantoms_json': self.renderer.render(phantoms_json.data),
        }

    def form_valid(self, form):
        machine = models.Machine.objects.get(pk=form.cleaned_data['machine'])
        sequence = models.Sequence.objects.get(pk=form.cleaned_data['sequence'])
        phantom = models.Phantom.objects.get(pk=form.cleaned_data['phantom'])

        scan = models.create_scan(
            machine,
            sequence,
            phantom,
            self.request.user,
            self.request.FILES['dicom_archive'],
            form.cleaned_data['notes'],
            form.cleaned_data['datasets'],
        )

        process_scan.delay(scan.pk)
        messages.success(self.request, "Your scan has been uploaded successfully and is processing.")
        return redirect('machine_sequence_detail', scan.machine_sequence_pair.pk)


@method_decorator(login_required, name='dispatch')
@validate_institution()
class ScanErrorsView(DetailView):
    model = models.Scan
    template_name = 'common/scan_errors.html'


def export_overlay(voxel_array, voxelSpacing_tup, voxelPosition_tup, studyInstanceUID, seriesInstanceUID, frameOfReferenceUID, patientID, output_directory):
    '''
    Exports a voxel array to a series of dicom files.

    :param voxel_array: voxels array in x,y,z axis order.
    :param voxelSpacing_tup: spacing in mm
    :param voxelPosition_tup: position of first voxel in mm in patient coordinate system
    :param studyInstanceUID:
    :param seriesInstanceUID:
    :param frameOfReferenceUID:
    :param patientID:
    :param output_directory: directory to dump the dicoms in
    :return:
    '''
    def _encode_multival(values):
        '''
        Encodes a collection of multivalued elements in backslash separated syntax known by dicom spec.
        '''
        return '\\'.join(str(val) for val in values)

    def _base_ds():
        sopinst = generate_uid()
        file_meta = Dataset()
        file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.2'  # CT Image Storage
        file_meta.TransferSyntaxUID = '1.2.840.10008.1.2'  # Implicit VR Little Endian
        file_meta.MediaStorageSOPInstanceUID = sopinst
        file_meta.ImplementationClassUID = '1.1.1'
        ds = FileDataset(None, {}, file_meta=file_meta, preamble=b"\0"*128)
        ds.SOPInstanceUID = sopinst
        ds.SOPClassUID = '1.2.840.10008.5.1.4.1.1.2'  # CT Image SOP Class
        return ds

    def _unstack(voxel_array):
        '''converts array of x,y,z into one of z,x,y to make it easier to slice.'''
        return voxel_array.transpose(2, 0, 1)

    if len(voxel_array.shape) != 3:
        raise Exception('Only 3d arrays are supported for dicom export, got shape {}'.format(voxel_array.shape))

    slices_array = _unstack(voxel_array)
    for slice_num, slice_arr in enumerate(slices_array):
        sliceVoxelPosition = (voxelPosition_tup[0],
                              voxelPosition_tup[1],
                              voxelPosition_tup[2] + voxelSpacing_tup[2]*slice_num)
        ds = _base_ds()
        # Patient Module
        ds.PatientName = ''
        ds.PatientID = patientID

        # general study module
        ds.ContentDate = str(datetime.today()).replace('-','')
        ds.ContentTime = str(time.time())
        ds.StudyInstanceUID = studyInstanceUID
        ds.StudyDescription = 'Distortion Overlay'

        # general series module
        ds.SeriesInstanceUID = seriesInstanceUID
        ds.Modality = 'PT'

        # Frame of reference module
        ds.FrameOfReferenceUID = frameOfReferenceUID

        # Image plane module
        xSpacing_mm, ySpacing_mm, zSpacing_mm = voxelSpacing_tup
        ds.ImageOrientationPatient = _encode_multival([1, 0, 0, 0, 1, 0])  # direction cosines
        ds.ImagePositionPatient = _encode_multival(sliceVoxelPosition)
        ds.PixelSpacing = _encode_multival([xSpacing_mm, ySpacing_mm])
        ds.SliceThickness = str(zSpacing_mm)
        ds.InstanceNumber = slice_num

        # image pixel module
        rows, columns = slice_arr.shape
        ds.SamplesPerPixel = 1
        ds.PhotometricInterpretation = "MONOCHROME2"
        ds.PixelRepresentation = 0  # unsigned int
        ds.HighBit = 15
        ds.BitsStored = 16
        ds.BitsAllocated = 16
        ds.Columns = columns
        ds.Rows = rows
        ds.NumberOfFrames = 1
        ds.RescaleIntercept = 0
        ds.RescaleSlope = 0.01
        ds.PixelData = slice_arr.astype(np.uint16).tobytes()
        dicom.write_file(os.path.join(output_directory, '{}.dcm'.format(ds.SOPInstanceUID)), ds)


@method_decorator(login_required, name='dispatch')
@validate_institution(model_class=models.Scan)
class DicomOverlayView(FormView):
    form_class = forms.DicomOverlayForm
    template_name = 'common/dicom_overlay.html'

    @cached_property
    def scan(self):
        return get_object_or_404(models.Scan, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super(DicomOverlayView, self).get_context_data(**kwargs)
        context.update({'scan': self.scan})
        return context

    def get_success_url(self):
        return reverse('machine_sequence_detail', args=(self.scan.machine_sequence_pair.pk,))

    def form_valid(self, form):
        # TODO: Consolidate and split out these constants in the process module.
        GRID_DENSITY_mm = 1
        DISTORTION_SCALE = 1000
        BLUR_SIGMA = 2
        ds = self.get_context_data()['scan'].dicom_series
        ijk_to_xyz = ds.ijk_to_xyz
        coord_min_xyz, coord_max_xyz = apply_affine(ijk_to_xyz, np.array([(0.0,0.0,0.0), ds.shape]).T).T
        TP_A = self.get_context_data()['scan'].TP_A_S.fiducials
        error_mags = self.get_context_data()['scan'].error_mags
        grid_x, grid_y, grid_z = np.meshgrid(np.arange(coord_min_xyz[0], coord_max_xyz[0], GRID_DENSITY_mm),
                                             np.arange(coord_min_xyz[1], coord_max_xyz[1], GRID_DENSITY_mm),
                                             np.arange(coord_min_xyz[2], coord_max_xyz[2], GRID_DENSITY_mm))
        logger.info("Gridding data for overlay generation.")
        gridded = griddata(TP_A.T, error_mags.T, (grid_x, grid_y, grid_z), method='linear')
        gridded *= DISTORTION_SCALE  # rescale so it looks a bit better
        gridded = scipy.ndimage.filters.gaussian_filter(gridded, BLUR_SIGMA, truncate=2)  # TODO: remove this once we fix interpolation
        gridded[np.isnan(gridded)] = 0
        output_dir = tempfile.mkdtemp()
        logger.info("Exporting overlay to dicoms.")
        export_overlay(
            voxel_array=gridded,
            voxelSpacing_tup=(GRID_DENSITY_mm, GRID_DENSITY_mm, GRID_DENSITY_mm),
            voxelPosition_tup=coord_min_xyz,
            studyInstanceUID=form.cleaned_data['study_instance_uid'] or ds.study_uid,
            seriesInstanceUID=generate_uid(),
            frameOfReferenceUID=form.cleaned_data['frame_of_reference_uid'] or ds.frame_of_reference_uid,
            patientID=form.cleaned_data['patient_id'] or ds.patient_id,
            output_directory=output_dir
        )
        zip_bytes = io.BytesIO()
        with zipfile.ZipFile(zip_bytes, 'w', zipfile.ZIP_DEFLATED) as zf:
            for dirname, subdirs, files in os.walk(output_dir):
                zf.write(dirname)
                for filename in files:
                    zf.write(os.path.join(dirname, filename), arcname=filename)
        logger.info("done zipping generated dicoms.")
        return ZipResponse(zip_bytes, filename='overlay.zip')


@method_decorator(login_required, name='dispatch')
@validate_institution()
class DeleteScanView(CirsDeleteView):
    model = models.Scan

    def delete(self, request, *args, **kwargs):
        response = super(DeleteScanView, self).delete(request, *args, **kwargs)
        messages.success(self.request, f"""Scan for phantom
            \"{self.object.golden_fiducials.phantom.model.model_number} —
            {self.object.golden_fiducials.phantom.serial_number}\", captured on
            {formats.date_format(self.object.acquisition_date)}, has been deleted successfully.""")
        return response

    def get_success_url(self):
        return reverse('machine_sequence_detail', args=(self.object.machine_sequence_pair.pk,))


@login_and_permission_required('common.configuration')
class CreatePhantomView(JsonFormMixin, FormView):
    form_class = forms.CreatePhantomForm
    success_url = reverse_lazy('configuration')
    template_name = 'common/phantom_create.html'
    renderer = JSONRenderer()

    def __init__(self, **kwargs):
        self.object = None
        super(CreatePhantomView, self).__init__(**kwargs)

    def form_valid(self, form):
        self.object = form.save(institution=self.request.user.institution)
        messages.success(self.request, f"\"{self.object.name}\" has been created successfully.")
        return super(CreatePhantomView, self).form_valid(form)


@login_and_permission_required('common.configuration')
@validate_institution()
class UpdatePhantomView(UpdateView):
    model = models.Phantom
    fields = ('name',)
    template_name_suffix = '_update'
    pk_url_kwarg = 'phantom_pk'

    def form_valid(self, form):
        messages.success(self.request, f"\"{self.object.name}\" has been updated successfully.")
        return super(UpdatePhantomView, self).form_valid(form)

    def get_success_url(self):
        return reverse('update_phantom', args=(self.kwargs['phantom_pk'],))

    @property
    def golden_fiducials(self):
        return self.object.goldenfiducials_set.active().order_by('-created_on')


@login_and_permission_required('common.configuration')
@validate_institution()
class DeletePhantomView(CirsDeleteView):
    model = models.Phantom
    success_url = reverse_lazy('configuration')
    pk_url_kwarg = 'phantom_pk'

    def delete(self, request, *args, **kwargs):
        response = super(DeletePhantomView, self).delete(request, *args, **kwargs)
        messages.success(self.request, f"\"{self.object.name}\" has been deleted successfully.")
        return response


@login_and_permission_required('common.configuration')
class CreateMachineView(CreateView):
    model = models.Machine
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
class UpdateMachineView(UpdateView):
    model = models.Machine
    fields = ('name', 'model', 'manufacturer')
    success_url = reverse_lazy('configuration')
    template_name_suffix = '_update'

    def form_valid(self, form):
        messages.success(self.request, f"\"{self.object.name}\" has been updated successfully.")
        return super(UpdateMachineView, self).form_valid(form)


@login_and_permission_required('common.configuration')
@validate_institution()
class DeleteMachineView(CirsDeleteView):
    model = models.Machine
    success_url = reverse_lazy('configuration')

    def delete(self, request, *args, **kwargs):
        response = super(DeleteMachineView, self).delete(request, *args, **kwargs)
        messages.success(self.request, f"\"{self.object.name}\" has been deleted successfully.")
        return response


@login_and_permission_required('common.configuration')
class CreateSequenceView(CreateView):
    model = models.Sequence
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
class UpdateSequenceView(UpdateView):
    model = models.Sequence
    fields = ('name', 'instructions')
    success_url = reverse_lazy('configuration')
    template_name_suffix = '_update'

    def form_valid(self, form):
        messages.success(self.request, f"\"{self.object.name}\" has been updated successfully.")
        return super(UpdateSequenceView, self).form_valid(form)


@login_and_permission_required('common.configuration')
@validate_institution()
class DeleteSequenceView(CirsDeleteView):
    model = models.Sequence
    success_url = reverse_lazy('configuration')

    def delete(self, request, *args, **kwargs):
        response = super(DeleteSequenceView, self).delete(request, *args, **kwargs)
        messages.success(self.request, f"\"{self.object.name}\" has been deleted successfully.")
        return response


@login_and_permission_required('common.manage_users')
class CreateUserView(FormView):
    form_class = forms.CreateUserForm
    success_url = reverse_lazy('configuration')
    template_name = 'common/user_create.html'
    email_template_name = 'common/create_user_email.html'
    html_email_template_name = None
    subject_template_name = 'common/create_user_subject.txt'
    extra_email_context = None
    token_generator = default_token_generator
    from_email = None

    def form_valid(self, form):
        opts = {
            'use_https': self.request.is_secure(),
            'token_generator': self.token_generator,
            'from_email': self.from_email,
            'email_template_name': self.email_template_name,
            'subject_template_name': self.subject_template_name,
            'request': self.request,
            'html_email_template_name': self.html_email_template_name,
            'extra_email_context': self.extra_email_context,
        }
        self.object = form.save(institution=self.request.user.institution, **opts)
        messages.success(self.request, f"\"{self.object.get_full_name()}\" has been created successfully.")
        return super(CreateUserView, self).form_valid(form)


@login_and_permission_required('common.manage_users')
@validate_institution()
class DeleteUserView(CirsDeleteView):
    model = models.User
    success_url = reverse_lazy('configuration')

    def delete(self, request, *args, **kwargs):
        response = super(DeleteUserView, self).delete(request, *args, **kwargs)
        messages.success(self.request, f"\"{self.object.get_full_name()}\" has been deleted successfully.")
        return response


@login_and_permission_required('common.configuration')
@validate_institution(model_class=models.Phantom, pk_url_kwarg='phantom_pk')
class UploadCTView(FormView):
    form_class = forms.UploadCTForm
    template_name = 'common/upload_ct.html'

    def form_valid(self, form):
        voxels, ijk_to_xyz = dicom_import.combine_slices(form.cleaned_data['datasets'])
        ds = form.cleaned_data['datasets'][0]
        dicom_series = models.DicomSeries.objects.create(
            zipped_dicom_files=self.request.FILES['dicom_archive'],
            voxels=voxels,
            ijk_to_xyz=ijk_to_xyz,
            shape=voxels.shape,
            series_uid=ds.SeriesInstanceUID,
            study_uid=ds.StudyInstanceUID,
            frame_of_reference_uid=ds.FrameOfReferenceUID,
            patient_id=ds.PatientID,
            # TODO: handle a missing AcquisitionDate
            acquisition_date=datetime.strptime(form.cleaned_data['datasets'][0].AcquisitionDate, '%Y%m%d'),
        )

        gold_standard = models.GoldenFiducials.objects.create(
            phantom=models.Phantom.objects.get(pk=self.kwargs['phantom_pk']),
            dicom_series=dicom_series,
            type=models.GoldenFiducials.CT,
            processing=True,
        )

        process_ct_upload.delay(dicom_series.pk, gold_standard.pk)
        messages.success(self.request, "Your gold standard CT has been uploaded successfully and is processing.")
        return super(UploadCTView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(UploadCTView, self).get_context_data(**kwargs)
        phantom = get_object_or_404(models.Phantom, pk=self.kwargs['phantom_pk'])
        context.update({'phantom': phantom})
        return context

    def get_success_url(self):
        return reverse('update_phantom', args=(self.kwargs['phantom_pk'],))


@login_and_permission_required('common.configuration')
@validate_institution(model_class=models.Phantom, pk_url_kwarg='phantom_pk')
class UploadRawView(FormView):
    form_class = forms.UploadRawForm
    template_name = 'common/upload_raw.html'

    def form_valid(self, form):
        phantom = models.Phantom.objects.get(pk=self.kwargs['phantom_pk'])
        fiducials = models.Fiducials.objects.create(fiducials=form.cleaned_data['fiducials'])
        models.GoldenFiducials.objects.create(
            phantom=phantom,
            fiducials=fiducials,
            type=models.GoldenFiducials.CSV,
        )
        messages.success(self.request, "Your gold standard points have been uploaded successfully.")
        return super(UploadRawView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(UploadRawView, self).get_context_data(**kwargs)
        phantom = get_object_or_404(models.Phantom, pk=self.kwargs['phantom_pk'])
        context.update({'phantom': phantom})
        return context

    def get_success_url(self):
        return reverse('update_phantom', args=(self.kwargs['phantom_pk'],))


@login_and_permission_required('common.configuration')
@validate_institution()
class DeleteGoldStandardView(CirsDeleteView):
    model = models.GoldenFiducials
    pk_url_kwarg = 'gold_standard_pk'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.type == models.GoldenFiducials.CAD or self.object.is_active:
            raise PermissionDenied
        else:
            messages.success(self.request, f"\"{self.object.source_summary}\" has been deleted successfully.")
            return super(DeleteGoldStandardView, self).delete(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('update_phantom', args=(self.kwargs['phantom_pk'],))

    def get_context_data(self, **kwargs):
        context = super(DeleteGoldStandardView, self).get_context_data(**kwargs)
        phantom = get_object_or_404(models.Phantom, pk=self.kwargs['phantom_pk'])
        context.update({'phantom': phantom})
        return context


@login_and_permission_required('common.configuration')
@validate_institution(model_class=models.GoldenFiducials, pk_url_kwarg='gold_standard_pk')
def activate_gold_standard_view(request, phantom_pk=None, gold_standard_pk=None):
    gold_standard = get_object_or_404(models.GoldenFiducials, pk=gold_standard_pk)
    gold_standard.activate()
    messages.success(request, f"\"{gold_standard.source_summary}\" has been activated successfully.")
    return redirect('update_phantom', phantom_pk)


@login_and_permission_required('common.configuration')
@validate_institution(model_class=models.GoldenFiducials, pk_url_kwarg='gold_standard_pk')
def gold_standard_csv_view(request, phantom_pk=None, gold_standard_pk=None):
    gold_standard = get_object_or_404(models.GoldenFiducials, pk=gold_standard_pk)
    return CSVResponse(gold_standard.fiducials.fiducials, filename=f'{gold_standard.source_summary}.csv')


def terms_of_use_view(request):
    return render(request, 'common/terms_of_use.html')


def privacy_policy_view(request):
    return render(request, 'common/privacy_policy.html')


@login_required
@validate_institution(model_class=models.Scan)
def refresh_scan_view(request, pk=None):
    if request.method == 'POST':
        scan = get_object_or_404(models.Scan, pk=pk)
        # TODO new image processing algorithm
        new_scan = models.Scan.objects.create(
            machine_sequence_pair=scan.machine_sequence_pair,
            dicom_series=scan.dicom_series,
            golden_fiducials=scan.golden_fiducials.phantom.active_gold_standard,
            tolerance=scan.machine_sequence_pair.tolerance,
            processing=True,
            creator=request.user,
            notes=scan.notes,
        )
        process_scan.delay(new_scan.pk)
        messages.success(request, "Scan is being re-run using the current tolerance threshold, phantom gold standard "
                                  "grid intersection locations, and image processing algorithm.")
        return redirect('machine_sequence_detail', new_scan.machine_sequence_pair.pk)
    else:
        return HttpResponseNotAllowed(['POST'])


# TODO JSON form errors, repopulate
class RegisterView(JsonFormMixin, FormView):
    form_class = forms.RegisterForm
    template_name = 'common/register.html'
    success_url = reverse_lazy('register_done')
    email_template_name = 'common/create_user_email.html'
    html_email_template_name = None
    subject_template_name = 'common/create_user_subject.txt'
    extra_email_context = None
    token_generator = default_token_generator
    from_email = None
    renderer = JSONRenderer()

    def form_valid(self, form):
        opts = {
            'use_https': self.request.is_secure(),
            'token_generator': self.token_generator,
            'from_email': self.from_email,
            'email_template_name': self.email_template_name,
            'subject_template_name': self.subject_template_name,
            'request': self.request,
            'html_email_template_name': self.html_email_template_name,
            'extra_email_context': self.extra_email_context,
        }
        form.save(**opts)
        return super(RegisterView, self).form_valid(form)


class RegisterDoneView(PasswordResetDoneView):
    template_name = 'common/register_done.html'


class CreatePasswordView(PasswordResetConfirmView):
    template_name = 'common/create_password.html'
    success_url = reverse_lazy('create_password_complete')


class CreatePasswordCompleteView(PasswordResetCompleteView):
    template_name = 'common/create_password_complete.html'

import logging

from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic.edit import CreateView, UpdateView, DeleteView, ModelFormMixin, FormView
from django.shortcuts import render, redirect
from django.urls import reverse_lazy

from .models import Scan, Phantom, Machine, Sequence, GoldenFiducials
from .tasks import process_scan
from .forms import UploadScanForm, UploadCTForm, UploadRawForm
from .decorators import check_institution, login_and_permission_required
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
        'phantoms': institution.phantom_set.filter(deleted=False),
        'machines': institution.machine_set.filter(deleted=False),
        'sequences': institution.sequence_set.filter(deleted=False),
        'users': institution.user_set.filter(deleted=False),
    })


@method_decorator(login_and_permission_required('common.configuration'), name='dispatch')
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


@method_decorator(login_and_permission_required('common.configuration'), name='dispatch')
@check_institution
class UpdatePhantom(UpdateView):
    model = Phantom
    fields = ('name',)
    success_url = reverse_lazy('configuration')
    template_name_suffix = '_update'
    pk_url_kwarg = 'phantom'


@method_decorator(login_and_permission_required('common.configuration'), name='dispatch')
@check_institution
class DeletePhantom(DeletionMixin, DeleteView):
    model = Phantom
    success_url = reverse_lazy('configuration')
    pk_url_kwarg = 'phantom'


@method_decorator(login_and_permission_required('common.configuration'), name='dispatch')
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


@method_decorator(login_and_permission_required('common.configuration'), name='dispatch')
@check_institution
class UpdateMachine(UpdateView):
    model = Machine
    fields = ('name', 'model', 'manufacturer')
    success_url = reverse_lazy('configuration')
    template_name_suffix = '_update'
    pk_url_kwarg = 'machine'


@method_decorator(login_and_permission_required('common.configuration'), name='dispatch')
@check_institution
class DeleteMachine(DeletionMixin, DeleteView):
    model = Machine
    success_url = reverse_lazy('configuration')
    pk_url_kwarg = 'machine'


@method_decorator(login_and_permission_required('common.configuration'), name='dispatch')
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


@method_decorator(login_and_permission_required('common.configuration'), name='dispatch')
@check_institution
class UpdateSequence(UpdateView):
    model = Sequence
    fields = ('name', 'instructions')
    success_url = reverse_lazy('configuration')
    template_name_suffix = '_update'
    pk_url_kwarg = 'sequence'


@method_decorator(login_and_permission_required('common.configuration'), name='dispatch')
@check_institution
class DeleteSequence(DeletionMixin, DeleteView):
    model = Sequence
    success_url = reverse_lazy('configuration')
    pk_url_kwarg = 'sequence'


@method_decorator(login_and_permission_required('common.configuration'), name='dispatch')
class GoldenFiducialsCTUpload(FormView):
    form_class = UploadCTForm
    template_name = 'common/upload_ct.html'


@method_decorator(login_and_permission_required('common.configuration'), name='dispatch')
class GoldenFiducialsRawUpload(FormView):
    form_class = UploadRawForm
    template_name = 'common/upload_raw.html'


@method_decorator(login_and_permission_required('common.configuration'), name='dispatch')
@check_institution
class DeleteGoldenFiducials(DeletionMixin, DeleteView):
    model = GoldenFiducials

    def get_success_url(self):
        return reverse('update_phantom', self.kwargs['phantom'])


@method_decorator(login_and_permission_required('common.configuration'), name='dispatch')
def set_active_golden_fiducials(request, phantom=None, gold=None):
    return redirect('update_phantom', phantom)


@login_and_permission_required('common.configuration')
def create_user(request):
    return render(request, 'common/user_create.html')


@login_and_permission_required('common.configuration')
def update_user(request, user=None):
    return render(request, 'common/user_update.html')


@login_and_permission_required('common.configuration')
def delete_user(request, user=None):
    return redirect('configuration')

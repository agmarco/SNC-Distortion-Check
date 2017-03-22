import logging

from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.views.generic.edit import CreateView, UpdateView, DeleteView, ModelFormMixin
from django.shortcuts import render, redirect
from django.urls import reverse_lazy

from .models import Scan, Phantom, Machine, Sequence, GoldenFiducials
from .tasks import process_scan
from .forms import UploadScanForm
from .factories import GoldenFiducialsFactory, FiducialsFactory

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


@login_required
@permission_required('common.configuration', raise_exception=True)
def configuration(request):
    institution = request.user.institution
    return render(request, 'common/configuration.html', {
        'phantoms': institution.phantom_set.filter(deleted=False),
        'machines': institution.machine_set.filter(deleted=False),
        'sequences': institution.sequence_set.filter(deleted=False),
        'users': institution.user_set.filter(deleted=False),
    })


@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('common.configuration', raise_exception=True), name='dispatch')
class CreatePhantom(CreateView):
    model = Phantom
    fields = ('name', 'model', 'serial_number')
    success_url = reverse_lazy('configuration')
    template_name_suffix = '_create'

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.institution = self.request.user.institution
        self.object.save()

        # create a golden fiducials object that points to the CAD model for the selected phantom model
        fiducials = FiducialsFactory()
        golden_fiducials = GoldenFiducialsFactory(
            phantom=self.object,
            fiducials=fiducials,
            cad_model=self.object.model.cad_model,
            source_type=GoldenFiducials.CAD,
            is_active=True,
        )

        return super(ModelFormMixin, self).form_valid(form)


@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('common.configuration', raise_exception=True), name='dispatch')
class UpdatePhantom(UpdateView):
    model = Phantom
    fields = ('name',)
    success_url = reverse_lazy('configuration')
    template_name_suffix = '_update'

    def dispatch(self, request, *args, **kwargs):
        object = self.get_object()
        if object.institution != self.request.user.institution:
            raise PermissionDenied
        return super(UpdatePhantom, self).dispatch(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('common.configuration', raise_exception=True), name='dispatch')
class DeletePhantom(DeleteView):
    model = Phantom
    success_url = reverse_lazy('configuration')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.deleted = True
        self.object.save()
        return HttpResponseRedirect(success_url)

    def dispatch(self, request, *args, **kwargs):
        object = self.get_object()
        if object.institution != self.request.user.institution:
            raise PermissionDenied
        return super(DeletePhantom, self).dispatch(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('common.configuration', raise_exception=True), name='dispatch')
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


@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('common.configuration', raise_exception=True), name='dispatch')
class UpdateMachine(UpdateView):
    model = Machine
    fields = ('name', 'model', 'manufacturer')
    success_url = reverse_lazy('configuration')
    template_name_suffix = '_update'

    def dispatch(self, request, *args, **kwargs):
        object = self.get_object()
        if object.institution != self.request.user.institution:
            raise PermissionDenied
        return super(UpdateMachine, self).dispatch(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('common.configuration', raise_exception=True), name='dispatch')
class DeleteMachine(DeleteView):
    model = Machine
    success_url = reverse_lazy('configuration')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.deleted = True
        self.object.save()
        return HttpResponseRedirect(success_url)

    def dispatch(self, request, *args, **kwargs):
        object = self.get_object()
        if object.institution != self.request.user.institution:
            raise PermissionDenied
        return super(DeleteMachine, self).dispatch(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('common.configuration', raise_exception=True), name='dispatch')
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


@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('common.configuration', raise_exception=True), name='dispatch')
class UpdateSequence(UpdateView):
    model = Sequence
    fields = ('name', 'instructions')
    success_url = reverse_lazy('configuration')
    template_name_suffix = '_update'

    def dispatch(self, request, *args, **kwargs):
        object = self.get_object()
        if object.institution != self.request.user.institution:
            raise PermissionDenied
        return super(UpdateSequence, self).dispatch(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('common.configuration', raise_exception=True), name='dispatch')
class DeleteSequence(DeleteView):
    model = Sequence
    success_url = reverse_lazy('configuration')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.deleted = True
        self.object.save()
        return HttpResponseRedirect(success_url)

    def dispatch(self, request, *args, **kwargs):
        object = self.get_object()
        if object.institution != self.request.user.institution:
            raise PermissionDenied
        return super(DeleteSequence, self).dispatch(request, *args, **kwargs)


@login_required
def create_user(request):
    return render(request, 'common/user_create.html')


@login_required
def update_user(request, pk):
    return render(request, 'common/user_update.html')


@login_required
def delete_user(request, pk):
    return redirect('configuration')

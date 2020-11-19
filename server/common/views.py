import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordResetConfirmView, PasswordResetCompleteView, \
        PasswordResetDoneView
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.core.mail import send_mail
from django.http import HttpResponseRedirect, HttpResponseNotAllowed
from django.template import loader
from django.urls import reverse, reverse_lazy
from django.utils import formats
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.views import View
from django.views.generic import DetailView, TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, ModelFormMixin, FormView
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth import views as auth_views
from rest_framework.renderers import JSONRenderer

from . import models
from . import serializers
from . import forms
from .tasks import process_scan, process_ct_upload, process_dicom_overlay, CT_WARNING_THRESHOLD
from .decorators import validate_institution, login_and_permission_required, institution_required, intro_tutorial, \
    check_license
from .http import CsvResponse

logger = logging.getLogger(__name__)


# TODO serialize help_text
class JsonFormMixin:
    """
    Only use this with classes that inherit from FormMixin.
    """

    renderer = JSONRenderer()
    form_class = None

    def get_context_data(self, **kwargs):
        context = super(JsonFormMixin, self).get_context_data(**kwargs)
        form_class = self.get_form_class()
        form = context['form']
        context.update({
            'form_initial': self.renderer.render(
                {name: form[name].value() or '' for name in form_class.base_fields.keys()}
            ),
        })
        return context

    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        context.update({
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


def fake_server_error(request):
    '''
    This view is for testing the 500 error page.
    '''
    raise ValueError()


@method_decorator(login_required, name='dispatch')
@method_decorator(institution_required, name='dispatch')
@method_decorator(intro_tutorial, name='dispatch')
@method_decorator(check_license(), name='dispatch')
class LandingView(TemplateView):
    template_name = 'common/landing.html'

    def get_context_data(self, **kwargs):
        context = super(LandingView, self).get_context_data(**kwargs)
        renderer = JSONRenderer()
        context.update({
            'machine_sequence_pairs_json': renderer.render(self.machine_sequence_pairs_data()),
        })
        return context

    def machine_sequence_pairs_data(self):
        institution = self.request.user.get_institution(self.request)
        base_queryset = models.MachineSequencePair.objects.filter(machine__institution=institution)
        active_queryset = base_queryset.active().filter(
            machine__deleted=False,
            sequence__deleted=False,
        )
        queryset = active_queryset.order_by('-last_modified_on')
        return serializers.MachineSequencePairSerializer(queryset, many=True).data


@login_and_permission_required('common.configuration')
@method_decorator(institution_required, name='dispatch')
@method_decorator(intro_tutorial, name='dispatch')
@method_decorator(check_license(), name='dispatch')
class ConfigurationView(UpdateView):
    model = models.Institution
    form_class = forms.InstitutionForm
    success_url = reverse_lazy('configuration')
    template_name = 'common/configuration.html'

    def get_object(self, queryset=None):
        return self.request.user.get_institution(self.request)

    def form_valid(self, form):
        messages.success(self.request, f"\"{self.object.name}\" has been updated.")
        return super(ConfigurationView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(ConfigurationView, self).get_context_data(**kwargs)
        institution = self.get_object()
        context.update({
            'phantoms': institution.phantom_set.active().order_by('-last_modified_on'),
            'machines': institution.machine_set.active().order_by('-last_modified_on'),
            'sequences': institution.sequence_set.active().order_by('-last_modified_on'),
            'institution': institution,
        })
        if self.request.user.has_perm('common.manage_users'):
            context['users'] = institution.user_set.active().order_by('-last_modified_on')
        return context


@method_decorator(login_required, name='dispatch')
@method_decorator(intro_tutorial, name='dispatch')
@method_decorator(check_license(), name='dispatch')
class AccountView(UpdateView):
    model = models.User
    form_class = forms.AccountForm
    success_url = reverse_lazy('account')
    template_name = 'common/account.html'

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Your account has been updated.")
        return super(AccountView, self).form_valid(form)


@method_decorator(login_required, name='dispatch')
@method_decorator(institution_required, name='dispatch')
@validate_institution()
@method_decorator(intro_tutorial, name='dispatch')
@method_decorator(check_license(), name='dispatch')
class MachineSequenceDetailView(DetailView):
    model = models.MachineSequencePair
    template_name = 'common/machine_sequence_detail.html'

    def get_context_data(self, **kwargs):
        context = super(MachineSequenceDetailView, self).get_context_data(**kwargs)
        machine_sequence_pair_json = serializers.MachineSequencePairSerializer(self.object)
        scans = models.Scan.objects.filter(machine_sequence_pair=self.object).active()
        scans_json = serializers.ScanSerializer(scans, many=True)

        renderer = JSONRenderer()
        context.update({
            'machine_sequence_pair': self.object,
            'machine_sequence_pair_json': renderer.render(machine_sequence_pair_json.data),
            'scans_json': renderer.render(scans_json.data),
        })
        return context

# @method_decorator(manage_worker_server, name='dispatch')
@method_decorator(login_required, name='dispatch')
@method_decorator(institution_required, name='dispatch')
@method_decorator(intro_tutorial, name='dispatch')
@method_decorator(check_license(check_scans=True), name='dispatch')
class UploadScanView(JsonFormMixin, FormView):
    form_class = forms.UploadScanForm
    template_name = 'common/upload_scan.html'
    renderer = JSONRenderer()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['institution'] = self.request.user.get_institution(self.request)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(UploadScanView, self).get_context_data(**kwargs)
        form = context['form']
        machines_json = serializers.MachineSerializer(form.fields['machine'].queryset, many=True)
        sequences_json = serializers.SequenceSerializer(form.fields['sequence'].queryset, many=True)
        phantoms_json = serializers.PhantomSerializer(form.fields['phantom'].queryset, many=True)
        context.update({
            'machines_json': self.renderer.render(machines_json.data),
            'sequences_json': self.renderer.render(sequences_json.data),
            'phantoms_json': self.renderer.render(phantoms_json.data),
        })
        return context

    def form_valid(self, form):
        machine = form.cleaned_data['machine']
        sequence = form.cleaned_data['sequence']
        phantom = form.cleaned_data['phantom']

        # TODO: check that the uploaded DICOM is an MRI (we can't support DICOM
        # Secondary Captures here, like we do for CT uploads)
        scan = models.create_scan(
            machine,
            sequence,
            phantom,
            self.request.user,
            notes=form.cleaned_data['notes'],
        )

        process_scan.delay(scan.pk, form.cleaned_data['dicom_archive_url'])
        messages.success(self.request, "Your scan has been uploaded.  Processing will likely take several minutes. "
                                       "This page will be updated automatically when it is finished.")
        return redirect('machine_sequence_detail', scan.machine_sequence_pair.pk)


# @manage_worker_server
@login_required
@institution_required
@validate_institution(model_class=models.Scan)
@check_license(check_scans=True)
def refresh_scan_view(request, pk=None):
    if request.method == 'POST':
        scan = get_object_or_404(models.Scan, pk=pk)
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
                                  "grid intersection locations, and image processing algorithm.  Processing will "
                                  "likely take several minutes.")
        return redirect('machine_sequence_detail', new_scan.machine_sequence_pair.pk)
    else:
        return HttpResponseNotAllowed(['POST'])


@method_decorator(login_required, name='dispatch')
@method_decorator(institution_required, name='dispatch')
@validate_institution()
@method_decorator(intro_tutorial, name='dispatch')
@method_decorator(check_license(), name='dispatch')
class ScanErrorsView(DetailView):
    model = models.Scan
    template_name = 'common/scan_errors.html'


@method_decorator(login_required, name='dispatch')
@method_decorator(institution_required, name='dispatch')
@validate_institution()
@method_decorator(intro_tutorial, name='dispatch')
@method_decorator(check_license(), name='dispatch')
class GoldStandardErrorsView(DetailView):
    pk_url_kwarg = 'gold_standard_pk'
    model = models.GoldenFiducials
    template_name = 'common/gold_standard_errors.html'


@method_decorator(login_required, name='dispatch')
@method_decorator(institution_required, name='dispatch')
@validate_institution(model_class=models.Scan)
@method_decorator(intro_tutorial, name='dispatch')
@method_decorator(check_license(), name='dispatch')
# @method_decorator(manage_worker_server, name='dispatch')
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
        return reverse('dicom_overlay_success', args=(self.scan.pk,))

    def form_valid(self, form):
        current_site = get_current_site(self.request)
        process_dicom_overlay.delay(
            self.get_context_data()['scan'].pk,
            form.cleaned_data['study_instance_uid'],
            form.cleaned_data['frame_of_reference_uid'],
            form.cleaned_data['patient_id'],
            self.request.user.email,
            current_site.domain,
            current_site.name,
            self.request.is_secure(),
        )
        return super(DicomOverlayView, self).form_valid(form)


@method_decorator(login_required, name='dispatch')
@method_decorator(institution_required, name='dispatch')
@validate_institution(model_class=models.Scan)
@method_decorator(intro_tutorial, name='dispatch')
@method_decorator(check_license(), name='dispatch')
class DicomOverlaySuccessView(TemplateView):
    template_name = 'common/dicom_overlay_success.html'

    def get_context_data(self, **kwargs):
        context = super(DicomOverlaySuccessView, self).get_context_data(**kwargs)
        scan = get_object_or_404(models.Scan, pk=self.kwargs['pk'])
        context.update({'scan': scan})
        return context


@method_decorator(login_required, name='dispatch')
@method_decorator(institution_required, name='dispatch')
@validate_institution()
@method_decorator(intro_tutorial, name='dispatch')
@method_decorator(check_license(), name='dispatch')
class DeleteScanView(CirsDeleteView):
    model = models.Scan

    def delete(self, request, *args, **kwargs):
        response = super(DeleteScanView, self).delete(request, *args, **kwargs)
        success_message = f"""Scan for phantom
            \"{self.object.golden_fiducials.phantom.model.model_number} —
            {self.object.golden_fiducials.phantom.serial_number}\""""
        if self.object.acquisition_date:
            success_message += f", captured on {formats.date_format(self.object.acquisition_date)}"
        success_message += ", has been deleted."
        messages.success(self.request, success_message)
        return response

    def get_success_url(self):
        return reverse('machine_sequence_detail', args=(self.object.machine_sequence_pair.pk,))


@login_and_permission_required('common.configuration')
@method_decorator(institution_required, name='dispatch')
@method_decorator(intro_tutorial, name='dispatch')
@method_decorator(check_license(), name='dispatch')
class CreatePhantomView(JsonFormMixin, FormView):
    form_class = forms.CreatePhantomForm
    success_url = reverse_lazy('configuration')
    template_name = 'common/phantom_create.html'

    def __init__(self, **kwargs):
        self.object = None
        super(CreatePhantomView, self).__init__(**kwargs)

    def form_valid(self, form):
        self.object = form.save(institution=self.request.user.get_institution(self.request))
        messages.success(self.request, f"\"{self.object.name}\" has been created.")
        return super(CreatePhantomView, self).form_valid(form)


@login_and_permission_required('common.configuration')
@method_decorator(institution_required, name='dispatch')
@validate_institution()
@method_decorator(intro_tutorial, name='dispatch')
@method_decorator(check_license(), name='dispatch')
class UpdatePhantomView(JsonFormMixin, UpdateView):
    model = models.Phantom
    fields = ('name',)
    template_name_suffix = '_update'
    pk_url_kwarg = 'phantom_pk'

    def form_valid(self, form):
        messages.success(self.request, f"\"{self.object.name}\" has been updated.")
        return super(UpdatePhantomView, self).form_valid(form)

    def get_success_url(self):
        return reverse('update_phantom', args=(self.kwargs['phantom_pk'],))

    def get_context_data(self, **kwargs):
        context = super(UpdatePhantomView, self).get_context_data(**kwargs)
        phantom_json = serializers.PhantomSerializer(self.object)
        golden_fiducials_set_json = self.object.goldenfiducials_set.active().order_by('-created_on')
        golden_fiducials_set_json = serializers.GoldenFiducialsSerializer(golden_fiducials_set_json, many=True)

        renderer = JSONRenderer()
        context.update({
            'phantom_json': renderer.render(phantom_json.data),
            'golden_fiducials_set_json': renderer.render(golden_fiducials_set_json.data),
        })
        return context

    @property
    def golden_fiducials(self):
        return self.object.goldenfiducials_set.active().order_by('-created_on')


@login_and_permission_required('common.configuration')
@method_decorator(institution_required, name='dispatch')
@validate_institution()
@method_decorator(intro_tutorial, name='dispatch')
@method_decorator(check_license(), name='dispatch')
class DeletePhantomView(CirsDeleteView):
    model = models.Phantom
    success_url = reverse_lazy('configuration')
    pk_url_kwarg = 'phantom_pk'

    def delete(self, request, *args, **kwargs):
        response = super(DeletePhantomView, self).delete(request, *args, **kwargs)
        messages.success(self.request, f"\"{self.object.name}\" has been deleted.")
        return response


@login_and_permission_required('common.configuration')
@method_decorator(institution_required, name='dispatch')
@method_decorator(intro_tutorial, name='dispatch')
@method_decorator(check_license(), name='dispatch')
class CreateMachineView(CreateView):
    form_class = forms.CreateMachineForm
    success_url = reverse_lazy('configuration')
    template_name = 'common/machine_create.html'

    def get_form_kwargs(self):
        kwargs = super(CreateMachineView, self).get_form_kwargs()
        kwargs.update({'institution': self.request.user.get_institution(self.request)})
        return kwargs

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f"\"{self.object.name}\" has been created.")
        return super(ModelFormMixin, self).form_valid(form)


@login_and_permission_required('common.configuration')
@method_decorator(institution_required, name='dispatch')
@validate_institution()
@method_decorator(intro_tutorial, name='dispatch')
@method_decorator(check_license(), name='dispatch')
class UpdateMachineView(UpdateView):
    model = models.Machine
    fields = ('name', 'model', 'manufacturer')
    success_url = reverse_lazy('configuration')
    template_name_suffix = '_update'

    def form_valid(self, form):
        messages.success(self.request, f"\"{self.object.name}\" has been updated.")
        return super(UpdateMachineView, self).form_valid(form)


@login_and_permission_required('common.configuration')
@method_decorator(institution_required, name='dispatch')
@validate_institution()
@method_decorator(intro_tutorial, name='dispatch')
@method_decorator(check_license(), name='dispatch')
class DeleteMachineView(CirsDeleteView):
    model = models.Machine
    success_url = reverse_lazy('configuration')

    def delete(self, request, *args, **kwargs):
        response = super(DeleteMachineView, self).delete(request, *args, **kwargs)
        messages.success(self.request, f"\"{self.object.name}\" has been deleted.")
        return response


@login_and_permission_required('common.configuration')
@method_decorator(institution_required, name='dispatch')
@method_decorator(intro_tutorial, name='dispatch')
@method_decorator(check_license(), name='dispatch')
class CreateSequenceView(CreateView):
    model = models.Sequence
    form_class = forms.SequenceForm
    success_url = reverse_lazy('configuration')
    template_name = 'common/sequence_create.html'

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.institution = self.request.user.get_institution(self.request)
        self.object.save()
        messages.success(self.request, f"\"{self.object.name}\" has been created.")
        return super(ModelFormMixin, self).form_valid(form)


@login_and_permission_required('common.configuration')
@method_decorator(institution_required, name='dispatch')
@validate_institution()
@method_decorator(intro_tutorial, name='dispatch')
@method_decorator(check_license(), name='dispatch')
class UpdateSequenceView(UpdateView):
    model = models.Sequence
    form_class = forms.SequenceForm
    success_url = reverse_lazy('configuration')
    template_name = 'common/sequence_update.html'

    def form_valid(self, form):
        messages.success(self.request, f"\"{self.object.name}\" has been updated.")
        return super(UpdateSequenceView, self).form_valid(form)


@login_and_permission_required('common.configuration')
@method_decorator(institution_required, name='dispatch')
@validate_institution()
@method_decorator(intro_tutorial, name='dispatch')
@method_decorator(check_license(), name='dispatch')
class DeleteSequenceView(CirsDeleteView):
    model = models.Sequence
    success_url = reverse_lazy('configuration')

    def delete(self, request, *args, **kwargs):
        response = super(DeleteSequenceView, self).delete(request, *args, **kwargs)
        messages.success(self.request, f"\"{self.object.name}\" has been deleted.")
        return response


@login_and_permission_required('common.manage_users')
@method_decorator(institution_required, name='dispatch')
@method_decorator(intro_tutorial, name='dispatch')
@method_decorator(check_license(), name='dispatch')
class CreateUserView(FormView):
    form_class = forms.CreateUserForm
    success_url = reverse_lazy('configuration')
    template_name = 'common/user_create.html'
    email_template_name = 'common/email/create_user_email.txt'
    html_email_template_name = 'common/email/create_user_email.html'
    subject_template_name = 'common/email/create_user_subject.txt'
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
        institution = self.request.user.get_institution(self.request)
        self.object = form.save(institution=institution, **opts)
        messages.success(self.request, f"\"{self.object.get_full_name()}\" has been created.")
        return super(CreateUserView, self).form_valid(form)


@login_and_permission_required('common.manage_users')
@method_decorator(institution_required, name='dispatch')
@validate_institution()
@method_decorator(intro_tutorial, name='dispatch')
@method_decorator(check_license(), name='dispatch')
class DeleteUserView(CirsDeleteView):
    model = models.User
    success_url = reverse_lazy('configuration')

    def delete(self, request, *args, **kwargs):
        if request.user == self.object:
            messages.warning(request, f"You can not delete yourself!")
            return redirect('configuration')
        else:
            response = super(DeleteUserView, self).delete(request, *args, **kwargs)
            messages.success(request, f"\"{self.object.get_full_name()}\" has been deleted.")
            return response


@login_and_permission_required('common.configuration')
@method_decorator(institution_required, name='dispatch')
@validate_institution(model_class=models.Phantom, pk_url_kwarg='phantom_pk')
@method_decorator(intro_tutorial, name='dispatch')
@method_decorator(check_license(check_scans=True), name='dispatch')
# @method_decorator(manage_worker_server, name='dispatch')
class UploadCtView(JsonFormMixin, FormView):
    form_class = forms.UploadCtForm
    template_name = 'common/upload_ct.html'

    def form_valid(self, form):
        gold_standard = models.GoldenFiducials.objects.create(
            phantom=models.Phantom.objects.get(pk=self.kwargs['phantom_pk']),
            type=models.GoldenFiducials.CT,
            processing=True,
            filename=form.cleaned_data['dicom_archive'],
        )

        process_ct_upload.delay(gold_standard.pk, form.cleaned_data['dicom_archive_url'])
        messages.success(self.request, "Your gold standard CT has been uploaded. "
                                       "Processing will likely take several minutes. "
                                       "This page will be updated automatically when it is finished.")
        return super(UploadCtView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(UploadCtView, self).get_context_data(**kwargs)
        phantom = get_object_or_404(models.Phantom, pk=self.kwargs['phantom_pk'])
        context.update({'phantom': phantom})
        return context

    def get_success_url(self):
        return reverse('update_phantom', args=(self.kwargs['phantom_pk'],))


@login_and_permission_required('common.configuration')
@method_decorator(institution_required, name='dispatch')
@validate_institution(model_class=models.Phantom, pk_url_kwarg='phantom_pk')
@method_decorator(intro_tutorial, name='dispatch')
@method_decorator(check_license(), name='dispatch')
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
            filename=form.cleaned_data['filename'],
        )
        messages.success(self.request, "Your gold standard points have been uploaded.")
        return super(UploadRawView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(UploadRawView, self).get_context_data(**kwargs)
        phantom = get_object_or_404(models.Phantom, pk=self.kwargs['phantom_pk'])
        context.update({'phantom': phantom})
        return context

    def get_success_url(self):
        return reverse('update_phantom', args=(self.kwargs['phantom_pk'],))


@login_and_permission_required('common.configuration')
@method_decorator(institution_required, name='dispatch')
@validate_institution()
@method_decorator(intro_tutorial, name='dispatch')
@method_decorator(check_license(), name='dispatch')
class DeleteGoldStandardView(CirsDeleteView):
    model = models.GoldenFiducials
    pk_url_kwarg = 'gold_standard_pk'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.type == models.GoldenFiducials.CAD or self.object.is_active:
            raise PermissionDenied
        else:
            messages.success(self.request, f"\"{self.object.source_summary}\" has been deleted.")
            return super(DeleteGoldStandardView, self).delete(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('update_phantom', args=(self.kwargs['phantom_pk'],))

    def get_context_data(self, **kwargs):
        context = super(DeleteGoldStandardView, self).get_context_data(**kwargs)
        phantom = get_object_or_404(models.Phantom, pk=self.kwargs['phantom_pk'])
        context.update({'phantom': phantom})
        return context


@login_and_permission_required('common.configuration')
@method_decorator(institution_required, name='dispatch')
@validate_institution(model_class=models.GoldenFiducials, pk_url_kwarg='gold_standard_pk')
@method_decorator(intro_tutorial, name='dispatch')
@method_decorator(check_license(), name='dispatch')
class ActivateGoldStandardView(View):
    def post(self, request, *args, phantom_pk=None, gold_standard_pk=None):
        gold_standard = get_object_or_404(models.GoldenFiducials, pk=gold_standard_pk)

        _, num_cad_points = gold_standard.phantom.model.cad_fiducials.fiducials.shape
        _, num_points = gold_standard.fiducials.fiducials.shape
        logger.info(f'Setting GoldenFiducials {gold_standard.pk} active, having points {num_points} ' + \
                    f'vs {num_cad_points} in the CAD')

        fractional_difference = abs(num_points - num_cad_points)/num_cad_points
        is_ct = gold_standard.type == models.GoldenFiducials.CT
        if fractional_difference > CT_WARNING_THRESHOLD:
            msg = f'"{gold_standard.source_summary}" is now active.  Note that it ' + \
                    f'contains {num_points} points, but the phantom model {gold_standard.phantom.model.name} ' + \
                    f'is expected to have roughly {num_cad_points} points.'
            if is_ct:
                msg += ' This mismatch in points may be due to issues with the image processing algorithm. ' + \
                        'CIRS has been notified of the result, and is looking into the failure.'

            messages.warning(request, msg)
        else:
            messages.success(request, f'"{gold_standard.source_summary}" is now active.')

        gold_standard.activate()
        return redirect('update_phantom', phantom_pk)


@login_and_permission_required('common.configuration')
@method_decorator(institution_required, name='dispatch')
@validate_institution(model_class=models.GoldenFiducials, pk_url_kwarg='gold_standard_pk')
@method_decorator(intro_tutorial, name='dispatch')
@method_decorator(check_license(), name='dispatch')
class GoldStandardCsvView(View):
    def get(self, request, *args, gold_standard_pk=None, **kwargs):
        gold_standard = get_object_or_404(models.GoldenFiducials, pk=gold_standard_pk)
        return CsvResponse(gold_standard.fiducials.fiducials, filename=f'{gold_standard.source_summary}.csv')


class TermsOfUseView(TemplateView):
    template_name = 'common/terms_of_use.html'


class PrivacyPolicyView(TemplateView):
    template_name = 'common/privacy_policy.html'


class RegisterView(JsonFormMixin, FormView):
    form_class = forms.RegisterForm
    template_name = 'common/register.html'
    success_url = reverse_lazy('register_done')
    email_template_name = 'common/email/create_user_email.txt'
    html_email_template_name = 'common/email/create_user_email.html'
    subject_template_name = 'common/email/create_user_subject.txt'
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
        self.object = form.save(**opts)

        institution = self.object.get_institution(self.request)
        current_site = get_current_site(self.request)
        protocol = 'https' if self.request.is_secure() else 'http'
        admin_path = reverse('admin:common_institution_change', args=(institution.pk,))
        admin_link = f'{protocol}://{current_site.domain}{admin_path}'
        context = {
            'admin_link': admin_link,
            'institution': institution,
            'phantom_serial_number': form.cleaned_data['phantom_serial_number'],
        }
        body = loader.render_to_string('common/email/create_user_cirs_email.txt', context)
        html_body = loader.render_to_string('common/email/create_user_cirs_email.html', context)
        send_mail(
            f'New User on CIRS Distortion Check for "{institution.name}"',
            body,
            settings.DEFAULT_FROM_EMAIL,
            [settings.DEFAULT_FROM_EMAIL],
            fail_silently=False,
            html_message=html_body,
        )

        return super(RegisterView, self).form_valid(form)


class RegisterDoneView(PasswordResetDoneView):
    template_name = 'common/register_done.html'


class CreatePasswordView(PasswordResetConfirmView):
    template_name = 'common/create_password.html'
    success_url = reverse_lazy('create_password_complete')


class CreatePasswordCompleteView(PasswordResetCompleteView):
    template_name = 'common/create_password_complete.html'


class PasswordResetView(auth_views.PasswordResetView):
    email_template_name = 'registration/email/password_reset_email.txt'
    html_email_template_name = 'registration/email/password_reset_email.html'
    subject_template_name = 'registration/email/password_reset_subject.txt'

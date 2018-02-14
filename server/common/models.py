import os
from datetime import datetime
import zipfile

import numpy as np

from django.db import models
from django.utils.functional import cached_property
from django.utils import timezone
from django.contrib import messages

from process import dicom_import

from server.django_numpy.fields import NdarrayTextField#, NdarrayFileField
from server.emailauth.models import AbstractUser, UserManager


class CommonFieldsSet(models.QuerySet):
    def active(self):
        return self.filter(deleted=False)


class CommonFieldsManager(models.Manager):
    def get_queryset(self):
        return CommonFieldsSet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()


class CommonFieldsMixin(models.Model):
    deleted_ht = 'Deleted items are hidden from non-admins'
    deleted = models.BooleanField(default=False, help_text=deleted_ht)
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified_on = models.DateTimeField(auto_now=True)

    objects = CommonFieldsManager()

    class Meta:
        abstract = True


class Institution(CommonFieldsMixin):
    name_ht = 'This is how the institution will be identified within the UI'
    name = models.CharField(max_length=255, help_text=name_ht)
    address = models.TextField()
    phone_number = models.CharField(max_length=255)
    license_expiration_date_ht = ("The date when the institution's license expires; "
            "they are warned 30 days before it expires.  If left blank, the license "
            "won't expire at a particular date.")
    license_expiration_date = models.DateField(null=True, blank=True, help_text=license_expiration_date_ht)
    scans_remaining_ht = ("The number of scans the institution is allowed to complete "
            "before needing to purchase more scans.  They are warned when there are 20 "
            "scans remaining.  Only successfully completed scans will decrement the count.  "
            "If left blank the license will never expire due to the scan count.")
    scans_remaining = models.PositiveIntegerField(null=True, blank=True, help_text=scans_remaining_ht)

    def __str__(self):
        return "{}".format(self.name)


class CommonFieldsUserManager(CommonFieldsManager, UserManager):
    pass


class User(AbstractUser, CommonFieldsMixin):
    institution_ht = 'The institution this user is a member of; will be blank for admin users'
    institution = models.ForeignKey(Institution, models.CASCADE, null=True, blank=True, help_text=institution_ht)

    objects = CommonFieldsUserManager()

    def get_institution(self, request):
        if self.institution:
            return self.institution
        elif self.is_superuser:
            institution_pk = request.session.get('institution')
            return institution_pk and Institution.objects.get(pk=institution_pk)
        else:
            return None


class Fiducials(CommonFieldsMixin):
    #fiducials = NdarrayFileField(upload_to='fiducials/fiducials')
    fiducials = NdarrayTextField()

    def __str__(self):
        return "Fiducials {}".format(self.id)

    class Meta:
        verbose_name = 'Fiducials'
        verbose_name_plural = 'Fiducials'


class PhantomModel(CommonFieldsMixin):
    name_ht = 'This is how the phantom model will be identified within the UI'
    name = models.CharField(max_length=255, help_text=name_ht)
    model_number_ht = 'The model number (e.g. 603A)'
    model_number = models.CharField(max_length=255, help_text=model_number_ht)
    cad_fiducials_ht = 'The hard-coded gold standard points for the phantom model'
    cad_fiducials = models.ForeignKey(Fiducials, models.CASCADE, help_text=cad_fiducials_ht)

    def __str__(self):
        return self.name


class Phantom(CommonFieldsMixin):
    name_ht = 'This is how the phantom will be identified within the UI'
    name = models.CharField(max_length=255, help_text=name_ht)
    institution_ht = 'The institution that owns this phantom.  If blank, new users can register an ' + \
        'account to the phantom if they know the serial number.'
    institution = models.ForeignKey(Institution, models.CASCADE, null=True, blank=True, help_text=institution_ht)
    model_ht = 'The model of phantom (e.g. the CIRS 603A head phantom)'
    model = models.ForeignKey(PhantomModel, models.CASCADE, help_text=model_ht)
    serial_number_ht = 'The Phantom\'s serial number'
    serial_number = models.CharField(max_length=255, unique=True, help_text=serial_number_ht)

    def __str__(self):
        return "Phantom {} {} {}".format(self.institution, self.model, self.name)

    @property
    def active_gold_standard(self):
        return self.goldenfiducials_set.get(is_active=True)


class Machine(CommonFieldsMixin):
    name_ht = 'This is how the machine will be identified within the UI'
    name = models.CharField(max_length=255, help_text=name_ht)
    model_ht = 'The model of the MR scanner (e.g. MAGNETOM Vida)'
    model = models.CharField(max_length=255, help_text=model_ht)
    manufacturer_ht = 'The company that manufactures the MR scanner (e.g. Siemens)'
    manufacturer = models.CharField(max_length=255, help_text=manufacturer_ht)
    institution = models.ForeignKey(Institution, models.CASCADE)

    def __str__(self):
        return "{}".format(self.name)


class Sequence(CommonFieldsMixin):
    name_ht = 'This is how the MR scan sequence type will be identified within the UI'
    name = models.CharField(max_length=255, help_text=name_ht)
    institution = models.ForeignKey(Institution, models.CASCADE)
    instructions_ht = 'Instructions describing how to capture this type of MR scan sequence'
    instructions = models.TextField(blank=True, default='', help_text=instructions_ht)
    tolerance_ht = "The default maximum allowable distortion (mm) for new machine-sequence pairs that use " \
                   "this sequence. The tolerance for a machine-sequence pair can be customized after the first " \
                   "scan is uploaded."
    tolerance = models.FloatField(default=3.0, help_text=tolerance_ht)

    def __str__(self):
        return "{}".format(self.name)


class MachineSequencePair(CommonFieldsMixin):
    machine = models.ForeignKey(Machine, models.CASCADE)
    sequence = models.ForeignKey(Sequence, models.CASCADE)
    tolerance_ht = 'The maximum allowable geometric distortion (mm) for this machine-scanner pair'
    tolerance = models.FloatField(help_text=tolerance_ht)

    def __str__(self):
        return "{} : {}".format(self.machine.name, self.sequence.name)

    @cached_property
    def latest_scan(self):
        return self.scan_set.active().first()

    @property
    def latest_scan_date(self):
        return self.latest_scan.acquisition_date if self.latest_scan else None

    @property
    def latest_scan_passed(self):
        return self.latest_scan.passed if self.latest_scan else None

    @property
    def institution(self):
        return self.machine.institution

    class Meta:
        verbose_name = 'Machine-Sequence Combination'


class DicomSeries(CommonFieldsMixin):
    zipped_dicom_files = models.FileField(upload_to='dicom_series/zipped_dicom_files')
    series_uid_ht = 'The DICOM Series Instance UID, which should uniquely identify a scan'
    series_uid = models.CharField(max_length=64, verbose_name='Series Instance UID', help_text=series_uid_ht)
    study_uid = models.CharField(max_length=64, verbose_name='Study Instance UID', help_text=series_uid_ht)
    frame_of_reference_uid = models.CharField(max_length=64, verbose_name='Frame Of Reference UID', help_text=series_uid_ht, blank=True, null=True)
    patient_id = models.CharField(max_length=64, verbose_name='Patient ID', help_text=series_uid_ht)
    acquisition_date_ht = 'The DICOM Series Instance Acquisition Date'
    acquisition_date = models.DateField(help_text=acquisition_date_ht, null=True)

    def __str__(self):
        return "DICOM Series {}".format(self.series_uid)

    @property
    def filename(self):
        return os.path.basename(self.zipped_dicom_files.name)

    def unzip_datasets(self):
        zipped_dicom_files = self.zipped_dicom_files
        zipped_dicom_files.seek(0)  # rewind the file, as it may have been read earlier
        with zipfile.ZipFile(zipped_dicom_files, 'r') as f:
            return dicom_import.dicom_datasets_from_zip(f)

    class Meta:
        verbose_name = 'DICOM Series'
        verbose_name_plural = 'DICOM Series'


class GoldenFiducials(CommonFieldsMixin):
    CAD = 'CAD'
    CT = 'CT'
    CSV = 'CSV'
    TYPE_CHOICES = (
        (CAD, 'CAD Model'),
        (CT, 'CT Scan'),
        (CSV, 'CSV Points'),
    )

    phantom = models.ForeignKey(Phantom, models.CASCADE)
    is_active = models.BooleanField(default=False)
    dicom_series = models.ForeignKey(DicomSeries, models.CASCADE, null=True)
    fiducials = models.ForeignKey(Fiducials, models.CASCADE, null=True)
    type_ht = 'The source type for the golden fiducials  (e.g. CT Scan or CAD Model).'
    type = models.CharField(max_length=3, choices=TYPE_CHOICES, help_text=type_ht)
    processing = models.BooleanField(default=False)
    filename = models.CharField(max_length=255)
    errors = models.TextField(null=True)

    def __str__(self):
        return "Golden Fiducials {}".format(self.id)

    def activate(self):
        current_gold_standard = self.phantom.active_gold_standard
        current_gold_standard.is_active = False
        current_gold_standard.save()

        self.is_active = True
        self.save()

    @property
    def source_summary(self):
        summary = self.get_type_display()
        if self.type == GoldenFiducials.CT and self.dicom_series:
            summary += f" Taken on {self.dicom_series.acquisition_date.strftime('%d %B %Y')}"
        elif self.type == GoldenFiducials.CSV:
            summary += f" Uploaded on {self.created_on.strftime('%d %B %Y')}"
        return summary

    @property
    def institution(self):
        return self.phantom.institution

    class Meta:
        verbose_name = 'Golden Fiducials'
        verbose_name_plural = 'Golden Fiducials'


def scan_upload_path(instance, filename):
    if not hasattr(instance, 'pk'):
        raise AttributeError("You must save the model before saving a FileField.")
    return os.path.join('scan', str(instance.pk), filename)


# TODO make sure FileFields are only accessible by users with the right permissions
# https://stackoverflow.com/questions/28166784/restricting-access-to-private-file-downloads-in-django
class Scan(CommonFieldsMixin):
    creator = models.ForeignKey(User, models.SET_NULL, null=True)
    machine_sequence_pair = models.ForeignKey(MachineSequencePair, models.CASCADE)
    dicom_series = models.ForeignKey(DicomSeries, models.CASCADE, null=True)
    detected_fiducials = models.ForeignKey(Fiducials, models.CASCADE, null=True)
    golden_fiducials = models.ForeignKey(GoldenFiducials, models.CASCADE)
    TP_A_S = models.ForeignKey(Fiducials, models.CASCADE, null=True, related_name='scan_tp_a_s_set')
    TP_B = models.ForeignKey(Fiducials, models.CASCADE, null=True, related_name='scan_tp_b_set')
    full_report = models.FileField(upload_to=scan_upload_path, null=True)
    executive_report = models.FileField(upload_to=scan_upload_path, null=True)
    raw_data = models.FileField(upload_to=scan_upload_path, null=True)
    notes = models.TextField(blank=True)
    processing = models.BooleanField(default=True)
    errors = models.TextField(null=True)
    tolerance = models.FloatField()

    def __str__(self):
        return f"Scan {self.pk}"

    @property
    def phantom(self):
        return self.golden_fiducials.phantom

    @property
    def institution(self):
        return self.creator.institution

    @cached_property
    def error_mags(self):
        if self.TP_A_S and self.TP_B:
            error_vecs = self.TP_A_S.fiducials - self.TP_B.fiducials
            return np.linalg.norm(error_vecs, axis=0)
        else:
            return None

    @property
    def passed(self):
        if not self.processing and self.errors is None:
            return self.error_mags.max() < self.tolerance
        else:
            return None

    @property
    def acquisition_date(self):
        try:
            return DicomSeries.objects.values_list('acquisition_date', flat=True).get(scan=self)
        except DicomSeries.DoesNotExist:
            return None

    class Meta:
        ordering = ('-dicom_series__acquisition_date', '-created_on')


# This table creates permissions that are not associated with a model.
class Global(models.Model):
    class Meta:
        managed = False
        permissions = (
            ('configuration', 'ConfigurationView'),
            ('manage_users', 'Manage Users'),
        )


def create_dicom_series(dicom_archive, request=None):
    with zipfile.ZipFile(dicom_archive, 'r') as dicom_archive_zipfile:
        dicom_datasets = dicom_import.dicom_datasets_from_zip(dicom_archive_zipfile)

    first_dataset = dicom_datasets[0]
    dicom_series = DicomSeries.objects.create(
        zipped_dicom_files=dicom_archive,
        series_uid=first_dataset.SeriesInstanceUID,
        study_uid=first_dataset.StudyInstanceUID,
        frame_of_reference_uid=first_dataset.FrameOfReferenceUID,
        patient_id=first_dataset.PatientID,
        acquisition_date=infer_acquisition_date(first_dataset, request),
    )
    dicom_series.save()
    return dicom_series


def create_scan(machine, sequence, phantom, creator, notes=''):
    machine_sequence_pair, _ = MachineSequencePair.objects.get_or_create(
        machine=machine,
        sequence=sequence,
        defaults={'tolerance': sequence.tolerance},
    )

    scan = Scan.objects.create(
        machine_sequence_pair=machine_sequence_pair,
        golden_fiducials=phantom.active_gold_standard,
        tolerance=machine_sequence_pair.tolerance,
        processing=True,
        creator=creator,
        notes=notes,
    )

    return scan


def infer_acquisition_date(dataset, request=None):
    '''
    We rely on the acquisition date for sorting and charting, but it is not a
    required DICOM attribute.  Hence, we infer it as the current date if
    necessary, and display a warning to the user.
    '''
    if hasattr(dataset, 'AcquisitionDate') and dataset.AcquisitionDate:
        acquisition_date = datetime.strptime(dataset.AcquisitionDate, '%Y%m%d')
    else:
        # the view should set this to the current date and warn the user; this
        # is set here only as a flag
        acquisition_date = timezone.now()
        if request:
            msg = "The uploaded DICOM file has no acquisition date, so the " + \
                    "current date was used instead."
            messages.info(request, msg)
    return acquisition_date

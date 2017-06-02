import os
from datetime import datetime
import zipfile

import numpy as np

from django.core.files import File
from django.db import models
from django.utils.functional import cached_property

from process import dicom_import
from server.django_numpy.fields import NumpyTextField
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
    number_of_licenses_ht = 'The number of machines that the institution is allowed to add'
    number_of_licenses = models.PositiveIntegerField(default=1, help_text=number_of_licenses_ht)
    address = models.TextField()
    phone_number = models.CharField(max_length=255)

    def __str__(self):
        return "{}".format(self.name)


class CommonFieldsUserManager(CommonFieldsManager, UserManager):
    pass


class User(AbstractUser, CommonFieldsMixin):
    institution_ht = 'The institution this user is a member of; will be blank for admin users'
    institution = models.ForeignKey(Institution, models.CASCADE, null=True, blank=True, help_text=institution_ht)

    objects = CommonFieldsUserManager()


class Fiducials(CommonFieldsMixin):
    #fiducials = NumpyTextField(upload_to='fiducials/fiducials')
    fiducials = NumpyTextField()

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
    institution = models.ForeignKey(Institution, models.CASCADE, null=True)
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
        return self.scan_set.active().order_by('-dicom_series__acquisition_date', '-created_on').first()

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
    voxels = NumpyTextField()
    ijk_to_xyz = NumpyTextField()
    shape = NumpyTextField()
    series_uid_ht = 'The DICOM Series Instance UID, which should uniquely identify a scan'
    series_uid = models.CharField(max_length=64, verbose_name='Series Instance UID', help_text=series_uid_ht)
    study_uid = models.CharField(max_length=64, verbose_name='Study Instance UID', help_text=series_uid_ht)
    frame_of_reference_uid = models.CharField(max_length=64, verbose_name='Frame Of Reference UID', help_text=series_uid_ht)
    patient_id = models.CharField(max_length=64, verbose_name='Patient ID', help_text=series_uid_ht)
    acquisition_date_ht = 'The DICOM Series Instance Acquisition Date'
    acquisition_date = models.DateField(help_text=acquisition_date_ht)

    def __str__(self):
        return "DICOM Series {}".format(self.series_uid)

    @property
    def filename(self):
        return os.path.basename(self.zipped_dicom_files.name)

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
        if self.type == GoldenFiducials.CT:
            return f"{self.get_type_display()} Taken on {self.dicom_series.acquisition_date.strftime('%d %B %Y')}"
        elif self.type == GoldenFiducials.CSV:
            return f"{self.get_type_display()} Uploaded on {self.created_on.strftime('%d %B %Y')}"
        else:
            return self.get_type_display()

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
    dicom_series = models.ForeignKey(DicomSeries, models.CASCADE)
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
        """Return True if the max error_mags is below the threshold."""
        return self.error_mags.max() < self.tolerance if self.error_mags is not None else None

    @property
    def acquisition_date(self):
        return DicomSeries.objects.values_list('acquisition_date', flat=True).get(scan=self)


# This table creates permissions that are not associated with a model.
class Global(models.Model):
    class Meta:
        managed = False
        permissions = (
            ('configuration', 'ConfigurationView'),
            ('manage_users', 'Manage Users'),
        )


def create_scan(machine, sequence, phantom, creator, dicom_archive, notes='', dicom_datasets=None):
    # TODO: grab tolerance from the sequence (will need to add a tolerance
    # field to the sequence)
    machine_sequence_pair, _ = MachineSequencePair.objects.get_or_create(
        machine=machine,
        sequence=sequence,
        defaults={'tolerance': 3},
    )

    if dicom_datasets is None:
        with zipfile.ZipFile(dicom_archive, 'r') as dicom_archive_zipfile:
            dicom_datasets = dicom_import.dicom_datasets_from_zip(dicom_archive_zipfile)

    voxels, ijk_to_xyz = dicom_import.combine_slices(dicom_datasets)
    ds = dicom_datasets[0]
    dicom_series = DicomSeries.objects.create(
        voxels=voxels,
        ijk_to_xyz=ijk_to_xyz,
        shape=voxels.shape,
        series_uid=ds.SeriesInstanceUID,
        study_uid=ds.StudyInstanceUID,
        frame_of_reference_uid=ds.FrameOfReferenceUID,
        patient_id=ds.PatientID,
        # TODO: handle a missing AcquisitionDate
        acquisition_date=datetime.strptime(dicom_datasets[0].AcquisitionDate, '%Y%m%d'),
    )

    dicom_series.zipped_dicom_files.save('dicom_archive', File(dicom_archive))

    scan = Scan.objects.create(
        machine_sequence_pair=machine_sequence_pair,
        dicom_series=dicom_series,
        golden_fiducials=phantom.active_gold_standard,
        tolerance=machine_sequence_pair.tolerance,
        processing=True,
        creator=creator,
        notes=notes,
    )

    return scan

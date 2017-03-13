from django.db import models
from django.contrib.auth.models import AbstractUser

from .fields import NumpyFileField, NumpyStrField


class StandardMixin(models.Model):
    deleted = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified_on = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Institution(models.Model, StandardMixin):
    name = models.CharField(max_length=255)
    number_of_licenses = models.PositiveIntegerField(default=1)

    def __str__(self):
        return "Institution {}".format(self.name)


class User(AbstractUser, StandardMixin):
    institution = models.ForeignKey(Institution, models.CASCADE, null=True, blank=True)


class Phantom(models.Model, StandardMixin):
    CIRS_603A = 'CIRS_603A'
    CIRS_604 = 'CIRS_604'
    MODEL_CHOICES = (
        (CIRS_603A, '603A'),
        (CIRS_604, '604'),
    )

    name = models.CharField(max_length=255)
    institution = models.ForeignKey(Institution, models.CASCADE)
    model = models.CharField(max_length=255, choices=MODEL_CHOICES)
    serial_number = models.CharField(max_length=255)

    def __str__(self):
        return "Phantom {} {} {}".format(self.institution, self.model, self.name)


class Machine(models.Model, StandardMixin):
    name = models.CharField(max_length=255)
    model = models.CharField(max_length=255)
    institution = models.ForeignKey(Institution, models.CASCADE)

    def __str__(self):
        return "Machine {} {} {}".format(self.institution, self.model, self.name)


class Sequence(models.Model, StandardMixin):
    name = models.CharField(max_length=255)
    institution = models.ForeignKey(Institution, models.CASCADE)
    instructions = models.TextField(blank=True, default='')

    def __str__(self):
        return "Sequence {} {} {}".format(self.institution, self.name)


class MachineSequencePair(models.Model, StandardMixin):
    machine = models.ForeignKey(Machine, models.CASCADE)
    sequence = models.ForeignKey(Sequence, models.CASCADE)
    tolerance = models.FloatField()

    def __str__(self):
        return "Machine Sequence Pair {} {} {}".format(
            self.machine.institution,
            self.machine.name,
            self.sequence.name,
        )


class DicomSeries(models.Model, StandardMixin):
    zipped_dicom_files = models.FileField(upload_to='dicom_series/zipped_dicom_files')
    voxels = NumpyFileField(upload_to='dicom_series/voxels')
    ijk_to_xyz = NumpyStrField()
    shape = NumpyStrField()
    series_uid = models.CharField(max_length=64)

    def __str__(self):
        return "Dicom Series {}".format(self.series_uid)


class Fiducials(models.Model, StandardMixin):
    fiducials = NumpyFileField(upload_to='fiducials/fiducials')

    def __str__(self):
        return "Fiducials {}".format(self.id)


class GoldenFiducials(models.Model, StandardMixin):
    phantom = models.ForeignKey(Phantom, models.CASCADE)
    dicom_series = models.ForeignKey(DicomSeries, models.CASCADE, null=True)
    fiducials = models.ForeignKey(Fiducials, models.CASCADE)

    def __str__(self):
        return "Golden Fiducials {}".format(self.id)


class Scan(models.Model, StandardMixin):
    creator = models.ForeignKey(User, models.SET_NULL)
    machine_sequence_pair = models.ForeignKey(MachineSequencePair, models.CASCADE)
    dicom_series = models.ForeignKey(DicomSeries, models.CASCADE)
    detected_fiducials = models.ForeignKey(Fiducials, models.CASCADE)
    golden_fiducials = models.ForeignKey(GoldenFiducials, models.CASCADE)

    # TODO: figure out how to store results
    result = models.TextField(null=True)
    processing = models.BooleanField(default=False)
    errors = models.TextField(null=True)
    tolerance = models.FloatField()

    def __str__(self):
        return "Scan {}".format(self.id)

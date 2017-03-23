from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager

from server.django_numpy.fields import NumpyTextField


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
    institution = models.ForeignKey(Institution, models.CASCADE)
    model_ht = 'The model of phantom (e.g. the CIRS 603A head phantom)'
    model = models.ForeignKey(PhantomModel, models.CASCADE, help_text=model_ht)
    serial_number_ht = 'The Phantom\'s serial number'
    serial_number = models.CharField(max_length=255, help_text=serial_number_ht)

    def __str__(self):
        return "Phantom {} {} {}".format(self.institution, self.model, self.name)

    @property
    def gold_standard(self):
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

    class Meta:
        verbose_name = 'Machine-Sequence Combination'


class DicomSeries(CommonFieldsMixin):
    zipped_dicom_files = models.FileField(upload_to='dicom_series/zipped_dicom_files')
    voxels = NumpyTextField()
    #voxels = NumpyFileField(upload_to='dicom_series/voxels')
    ijk_to_xyz = NumpyTextField()
    shape = NumpyTextField()
    series_uid_ht = 'The DICOM Series Instance UID, which should uniquely identify a scan'
    series_uid = models.CharField(max_length=64, verbose_name='Series Instance UID', help_text=series_uid_ht)
    acquisition_date_ht = 'The DICOM Series Instance Acquisition Date'
    acquisition_date = models.DateField(help_text=acquisition_date_ht)

    def __str__(self):
        return "DICOM Series {}".format(self.series_uid)

    class Meta:
        verbose_name = 'DICOM Series'
        verbose_name_plural = 'DICOM Series'


class GoldenFiducials(CommonFieldsMixin):
    CAD = 'CAD'
    CT = 'CT'
    RAW = 'RAW'
    TYPE_CHOICES = (
        (CAD, 'CAD Model'),
        (CT, 'CT Scan'),
        (RAW, 'Raw Points'),
    )

    phantom = models.ForeignKey(Phantom, models.CASCADE)
    is_active = models.BooleanField()
    dicom_series = models.ForeignKey(DicomSeries, models.CASCADE, null=True)
    fiducials = models.ForeignKey(Fiducials, models.CASCADE)
    type_ht = 'The source type for the golden fiducials  (e.g. CT Scan or CAD Model).'
    type = models.CharField(max_length=3, choices=TYPE_CHOICES, help_text=type_ht)

    def __str__(self):
        return "Golden Fiducials {}".format(self.id)

    def activate(self):
        current_gold_standard = self.phantom.gold_standard
        current_gold_standard.is_active = False
        current_gold_standard.save()

        self.is_active = True
        self.save()

    @property
    def source_summary(self):
        if self.type == GoldenFiducials.CT:
            return f"{self.get_type_display()} Taken on {self.dicom_series.acquisition_date.strftime('%d %B %Y')}"
        else:
            return self.get_type_display()

    @property
    def institution(self):
        return self.phantom.institution

    class Meta:
        verbose_name = 'Golden Fiducials'
        verbose_name_plural = 'Golden Fiducials'


class Scan(CommonFieldsMixin):
    creator = models.ForeignKey(User, models.SET_NULL, null=True)
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


# This table creates permissions that are not associated with a model.
class Global(models.Model):
    class Meta:
        managed = False
        permissions = (
            ('configuration', 'Configuration'),
        )

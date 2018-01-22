import datetime
import zipfile
import os

import numpy as np
import scipy.io
import factory

from process import file_io


class InstitutionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "common.Institution"

    name = "Johns Hopkins"


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "common.User"

    email = factory.Sequence('user{0}@example.com'.format)
    password = "password"

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        manager = cls._get_manager(model_class)
        return manager.create_user(*args, **kwargs)

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        """
        Add groups to the user using:

            group = GroupFactory('admin')
            UserFactory(groups=[group])

        """
        if not create:
            return

        if extracted:
            for group in extracted:
                self.groups.add(group)


class GroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "auth.Group"

    name = factory.Sequence("group{0}".format)

    @factory.post_generation
    def permissions(self, create, extracted, **kwargs):
        """
        Add permissions to the group using:

            permission = Permission.objects.get(codename='configuration')
            GroupFactory(permissions=[permission])
        """
        if not create:
            return

        if extracted:
            for permission in extracted:
                self.permissions.add(permission)


class MachineFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "common.Machine"

    name = factory.Sequence("Machine {0}".format)
    model = "MAGNETOM Vida"
    manufacturer = "Siemens"
    institution = factory.SubFactory(InstitutionFactory)


class FiducialsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "common.Fiducials"

    fiducials = np.random.rand(3, 10)


cad_603A_points = file_io.load_points('data/points/603A.mat')['points']
cad_603A_points.flags.writeable = False


class Fiducials603ACADFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "common.Fiducials"

    fiducials = cad_603A_points


class PhantomModelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "common.PhantomModel"

    cad_fiducials = factory.SubFactory(Fiducials603ACADFactory)
    model_number = '603A'
    name = 'Factory CIRS 603A'


class PhantomFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "common.Phantom"

    name = factory.Sequence("Machine {0}".format)
    model = factory.SubFactory(PhantomModelFactory)
    serial_number = factory.Sequence("SN{0}".format)

    @factory.post_generation
    def golden_fiducials(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for golden_fiducials in extracted:
                self.goldenfiducials_set.add(golden_fiducials)


class SequenceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "common.Sequence"

    name = factory.Sequence("Sequence {0}".format)
    instructions = 'Set the FOV and all of the gradients and everything the right way.'
    institution = factory.SubFactory(InstitutionFactory)


class MachineSequencePairFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "common.MachineSequencePair"

    machine = factory.SubFactory(MachineFactory)
    sequence = factory.SubFactory(SequenceFactory)
    tolerance = 3


def _get_acquisition_date_generator():
    start = datetime.date(2016, 11, 2)
    count = 0
    while True:
        yield start + datetime.timedelta(days=count)
        count += 1


_get_acquisition_date = _get_acquisition_date_generator()

sample_603A_mri_zip_filename = 'data/dicom/006_mri_603A_UVA_Axial_2ME2SRS5.zip'

class DicomSeriesFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "common.DicomSeries"

    series_uid = '1.2.840.113704.7.32.0.2.18.42499.2016082704404467665110076.0.0.0'
    study_uid = '1.3.12.2.1107.5.2.18.42499.30000016082707192095400000002'
    patient_id = '123$$$6650572'
    frame_of_reference_uid = '1.3.12.2.1107.5.2.18.42499.1.20160827043859866.0.0.0'
    acquisition_date = factory.LazyAttribute(lambda dicom_series: next(_get_acquisition_date))
    zipped_dicom_files = factory.django.FileField(from_path=sample_603A_mri_zip_filename)


class GoldenFiducialsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "common.GoldenFiducials"

    phantom = factory.SubFactory(PhantomFactory)
    fiducials = factory.SubFactory(Fiducials603ACADFactory)


class ScanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "common.Scan"

    creator = factory.SubFactory(UserFactory)
    machine_sequence_pair = factory.SubFactory(MachineSequencePairFactory)
    dicom_series = factory.SubFactory(DicomSeriesFactory)
    detected_fiducials = factory.SubFactory(FiducialsFactory)
    TP_A_S = factory.SubFactory(FiducialsFactory)
    TP_B = factory.SubFactory(FiducialsFactory)
    golden_fiducials = factory.SubFactory(GoldenFiducialsFactory)
    tolerance = 3

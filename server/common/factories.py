import datetime
import zipfile

import numpy as np
import factory


class InstitutionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "common.Institution"

    name = "Johns Hopkins"


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "common.User"

    username = factory.Sequence("user{0}".format)
    password = "password"
    email = factory.LazyAttribute(lambda u: '{}@example.com'.format(u.username))

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


class PhantomModelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "common.PhantomModel"

    cad_fiducials = factory.SubFactory(FiducialsFactory)


class PhantomFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "common.Phantom"

    name = factory.Sequence("Machine {0}".format)
    model = factory.SubFactory(PhantomModelFactory)
    serial_number = factory.Sequence("Serial Number {0}".format)


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


class DicomSeriesFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "common.DicomSeries"

    voxels = np.random.rand(10, 10, 10)
    ijk_to_xyz = np.random.rand(4, 4)
    shape = np.array([10, 10, 10])
    series_uid = '1.2.392.200193.3.1626980217.161129.153348.41538611151089740341'
    acquisition_date = datetime.date(2016, 11, 2)


class GoldenFiducialsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "common.GoldenFiducials"

    phantom = factory.SubFactory(PhantomFactory)
    fiducials = factory.SubFactory(FiducialsFactory)


class ScanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "common.Scan"

    creator = factory.SubFactory(UserFactory)
    machine_sequence_pair = factory.SubFactory(MachineSequencePairFactory)
    dicom_series = factory.SubFactory(DicomSeriesFactory)
    detected_fiducials = factory.SubFactory(FiducialsFactory)
    golden_fiducials = factory.SubFactory(GoldenFiducialsFactory)
    distortion = factory.LazyAttribute(lambda scan: np.array(list(max(0, x) for x in np.random.normal(1.2, 0.55, (10,)))))
    tolerance = 3

import factory

from .models import Phantom


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
        '''
        Add groups to the user using:

            group = GroupFactory('admin')
            UserFactory(groups=[group])

        '''
        if not create:
            return

        if extracted:
            for group in extracted:
                self.groups.add(group)


class GroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "auth.Group"

    name = factory.Sequence("group{0}".format)


class MachineFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "common.Machine"

    name = factory.Sequence("Machine {0}".format)
    model = "MAGNETOM Vida"
    manufacturer = "Siemens"
    institution = factory.SubFactory(InstitutionFactory)


class PhantomModelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "common.PhantomModel"


class PhantomFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "common.Phantom"

    name = factory.Sequence("Machine {0}".format)
    model = factory.SubFactory(PhantomModelFactory)
    institution = factory.SubFactory(InstitutionFactory)
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
    tolerance = 3.5


class DicomSeriesFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "common.DicomSeries"


class FiducialsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "common.Fiducials"


class GoldenFiducialsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "common.GoldenFiducials"

    phantom = factory.SubFactory(PhantomFactory)
    fiducials = factory.SubFactory(FiducialsFactory)
    dicom_series = factory.SubFactory(DicomSeriesFactory)

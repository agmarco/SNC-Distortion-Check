from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand, CommandError

from server.common.factories import (UserFactory, GroupFactory, InstitutionFactory, PhantomFactory, SequenceFactory, MachineSequencePairFactory,
                                     MachineFactory, DicomSeriesFactory, FiducialsFactory, GoldenFiducialsFactory)
from server.common.models import Phantom


class Command(BaseCommand):
    help = 'Load some test data into the database.'

    def handle(self, *args, **options):
        configuration_permission = Permission.objects.get(codename='configuration')

        medical_physicists = GroupFactory.create(name='Medical Physicist')
        medical_physicists.permissions.add(configuration_permission)
        therapists = GroupFactory.create(name='Therapist')

        admin = UserFactory.create(
            username="admin",
            email="admin@cirs.com",
            first_name="admin",
            last_name="cirs",
            is_staff=True,
            is_superuser=True
        )

        john_hopkins = InstitutionFactory.create(name='John Hopkins')

        medical_physicist = UserFactory.create(
            username="medical_physicist",
            first_name="Mary",
            last_name="Jane",
            email="mary.jane@johnhopkins.edu",
            institution=john_hopkins,
            groups=[medical_physicists],
        )

        therapist = UserFactory.create(
            username="therapist",
            first_name="John",
            last_name="Doe",
            email="john.doe@johnhopkins.edu",
            institution=john_hopkins,
            groups=[therapists],
        )

        machine_a = MachineFactory.create(
            name='MRI Scanner East',
            institution=john_hopkins,
        )
        machine_b = MachineFactory.create(
            name='MRI Scanner West',
            institution=john_hopkins,
        )

        phantom_a = PhantomFactory(
            name='Head Phantom 1',
            model=Phantom.CIRS_603A,
            institution=john_hopkins,
        )
        phantom_b = PhantomFactory(
            name='Head Phantom 2',
            model=Phantom.CIRS_603A,
            institution=john_hopkins,
        )
        phantom_c = PhantomFactory(
            name='Body Phantom',
            model=Phantom.CIRS_604,
            institution=john_hopkins,
        )

        sequence_a = SequenceFactory(
            name="T1-Weighted Abdominal",
            institution=john_hopkins,
        )
        sequence_b = SequenceFactory(
            name="T1-Weighted Neural",
            institution=john_hopkins,
        )
        sequence_c = SequenceFactory(
            name="T2-Weighted Neural",
            institution=john_hopkins,
        )

        machine_sequence_pair = MachineSequencePairFactory(
            sequence=sequence_a,
            machine=machine_a,
        )

        dicom_series = DicomSeriesFactory()

import os

from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand, CommandError
from django.core.files import File
from django.conf import settings

from server.common import factories
from server.common.models import Phantom, GoldenFiducials


class Command(BaseCommand):
    help = 'Load some test data into the database.'

    def handle(self, *args, **options):
        configuration_permission = Permission.objects.get(codename='configuration')

        medical_physicists = factories.GroupFactory.create(name='Medical Physicist')
        medical_physicists.permissions.add(configuration_permission)
        therapists = factories.GroupFactory.create(name='Therapist')

        admin = factories.UserFactory.create(
            username="admin",
            email="admin@cirs.com",
            first_name="admin",
            last_name="cirs",
            is_staff=True,
            is_superuser=True
        )

        john_hopkins = factories.InstitutionFactory.create(name='John Hopkins')

        medical_physicist = factories.UserFactory.create(
            username="medical_physicist",
            first_name="Mary",
            last_name="Jane",
            email="mary.jane@johnhopkins.edu",
            institution=john_hopkins,
            groups=[medical_physicists],
        )

        therapist = factories.UserFactory.create(
            username="therapist",
            first_name="John",
            last_name="Doe",
            email="john.doe@johnhopkins.edu",
            institution=john_hopkins,
            groups=[therapists],
        )

        machine_a = factories.MachineFactory.create(
            name='MRI Scanner East',
            institution=john_hopkins,
        )
        machine_b = factories.MachineFactory.create(
            name='MRI Scanner West',
            institution=john_hopkins,
        )

        phantom_a = factories.PhantomFactory(
            name='Head Phantom 1',
            model=Phantom.CIRS_603A,
            institution=john_hopkins,
        )
        phantom_b = factories.PhantomFactory(
            name='Head Phantom 2',
            model=Phantom.CIRS_603A,
            institution=john_hopkins,
        )
        phantom_c = factories.PhantomFactory(
            name='Body Phantom',
            model=Phantom.CIRS_604,
            institution=john_hopkins,
        )

        sequence_a = factories.SequenceFactory(
            name="T1-Weighted Abdominal",
            institution=john_hopkins,
        )
        sequence_b = factories.SequenceFactory(
            name="T1-Weighted Neural",
            institution=john_hopkins,
        )
        sequence_c = factories.SequenceFactory(
            name="T2-Weighted Neural",
            institution=john_hopkins,
        )

        machine_sequence_pair = factories.MachineSequencePairFactory(
            sequence=sequence_a,
            machine=machine_a,
        )

        dicom_series_a = factories.DicomSeriesFactory()
        with open(os.path.join(settings.BASE_DIR, 'data/dicom/001_ct_603A_E3148_ST1.25.zip'), 'rb') as dicom_file:
            dicom_series_a.zipped_dicom_files.save(f'dicom_series_{dicom_series_a.pk}.png', File(dicom_file))
        dicom_series_a.save()

        fiducials_a = factories.FiducialsFactory()
        fiducials_b = factories.FiducialsFactory()
        fiducials_c = factories.FiducialsFactory()

        golden_fiducials_a = factories.GoldenFiducialsFactory(
            phantom=phantom_a,
            fiducials=fiducials_a,
            dicom_series=dicom_series_a,
            source_type=GoldenFiducials.CT,
        )
        golden_fiducials_b = factories.GoldenFiducialsFactory(
            phantom=phantom_b,
            fiducials=fiducials_b,
            source_type=GoldenFiducials.CAD,
        )
        golden_fiducials_b = factories.GoldenFiducialsFactory(
            phantom=phantom_c,
            fiducials=fiducials_c,
            source_type=GoldenFiducials.CAD,
        )

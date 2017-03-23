import os

from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand
from django.core.files import File
from django.conf import settings

from server.common import factories
from server.common.models import GoldenFiducials


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

        johns_hopkins = factories.InstitutionFactory.create(name='Johns Hopkins')

        medical_physicist = factories.UserFactory.create(
            username="medical_physicist",
            first_name="Mary",
            last_name="Jane",
            email="mary.jane@johnhopkins.edu",
            institution=johns_hopkins,
            groups=[medical_physicists],
        )

        therapist = factories.UserFactory.create(
            username="therapist",
            first_name="John",
            last_name="Doe",
            email="john.doe@johnhopkins.edu",
            institution=johns_hopkins,
            groups=[therapists],
        )

        machine_a = factories.MachineFactory.create(
            name='MRI Scanner East',
            institution=johns_hopkins,
        )
        machine_b = factories.MachineFactory.create(
            name='MRI Scanner West',
            institution=johns_hopkins,
        )

        fiducials_a = factories.FiducialsFactory()
        fiducials_b = factories.FiducialsFactory()
        fiducials_c = factories.FiducialsFactory()
        fiducials_d = factories.FiducialsFactory()

        phantom_model_a = factories.PhantomModelFactory(
            name='CIRS 603A',
            model_number='603A',
            cad_fiducials=fiducials_a,
        )
        phantom_model_b = factories.PhantomModelFactory(
            name='CIRS 604',
            model_number='604',
            cad_fiducials=fiducials_b,
        )

        phantom_a = factories.PhantomFactory(
            name='Head Phantom 1',
            model=phantom_model_a,
            institution=johns_hopkins,
        )
        phantom_b = factories.PhantomFactory(
            name='Head Phantom 2',
            model=phantom_model_a,
            institution=johns_hopkins,
        )
        phantom_c = factories.PhantomFactory(
            name='Body Phantom',
            model=phantom_model_b,
            institution=johns_hopkins,
        )

        dicom_series = factories.DicomSeriesFactory()
        with open(os.path.join(settings.BASE_DIR, 'data/dicom/001_ct_603A_E3148_ST1.25.zip'), 'rb') as dicom_file:
            dicom_series.zipped_dicom_files.save(f'dicom_series_{dicom_series.pk}.zip', File(dicom_file))
            dicom_series.save()

        golden_fiducials_a = factories.GoldenFiducialsFactory(
            phantom=phantom_a,
            fiducials=fiducials_c,
            dicom_series=dicom_series,
            type=GoldenFiducials.CT,
            is_active=False,
        )
        golden_fiducials_b = factories.GoldenFiducialsFactory(
            phantom=phantom_a,
            fiducials=fiducials_d,
            type=GoldenFiducials.RAW,
            is_active=False,
        )

        sequence_a = factories.SequenceFactory(
            name="T1-Weighted Abdominal",
            institution=johns_hopkins,
        )
        sequence_b = factories.SequenceFactory(
            name="T1-Weighted Neural",
            institution=johns_hopkins,
        )
        sequence_c = factories.SequenceFactory(
            name="T2-Weighted Neural",
            institution=johns_hopkins,
        )

        machine_sequence_pair = factories.MachineSequencePairFactory(
            sequence=sequence_a,
            machine=machine_a,
        )

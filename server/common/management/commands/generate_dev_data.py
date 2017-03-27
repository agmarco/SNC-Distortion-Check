import os
import zipfile

import numpy as np

from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand
from django.core.files import File
from django.conf import settings

from process import dicom_import
from server.common import factories
from server.common.models import GoldenFiducials


class Command(BaseCommand):
    help = 'Load some test data into the database.'

    def handle(self, *args, **options):
        configuration_permission = Permission.objects.get(codename='configuration')
        manage_users_permission = Permission.objects.get(codename='manage_users')

        managers = factories.GroupFactory.create(name='Manager')
        managers.permissions.add(configuration_permission)
        managers.permissions.add(manage_users_permission)

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

        manager = factories.UserFactory.create(
            username="manager",
            first_name="Sergei",
            last_name="Rachmaninoff",
            email="sergei.rachmaninoff@johnhopkins.edu",
            institution=johns_hopkins,
            groups=[managers],
        )

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

        phantom_model_a = factories.PhantomModelFactory(
            name='CIRS 603A',
            model_number='603A',
        )
        phantom_model_b = factories.PhantomModelFactory(
            name='CIRS 604',
            model_number='604',
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

        dicom_filename = 'data/dicom/001_ct_603A_E3148_ST1.25.zip'
        with zipfile.ZipFile(dicom_filename, 'r') as zip_file:
            datasets = dicom_import.dicom_datasets_from_zip(zip_file)
        voxels, ijk_to_xyz = dicom_import.combine_slices(datasets)
        dicom_series = factories.DicomSeriesFactory(
            voxels=voxels,
            ijk_to_xyz=ijk_to_xyz,
            shape=voxels.shape,
            datasets=datasets,
        )
        with open(os.path.join(settings.BASE_DIR, dicom_filename), 'rb') as dicom_file:
            dicom_series.zipped_dicom_files.save(f'dicom_series_{dicom_series.pk}.zip', File(dicom_file))

        golden_fiducials_a = factories.GoldenFiducialsFactory(
            phantom=phantom_a,
            dicom_series=dicom_series,
            type=GoldenFiducials.CT,
        )
        golden_fiducials_b = factories.GoldenFiducialsFactory(
            phantom=phantom_a,
            type=GoldenFiducials.RAW,
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

import os
import uuid
import zipfile
from random import randint

import numpy as np

from django.conf import settings
from django.contrib.auth.models import Permission
from django.core.files import File
from django.core.management.base import BaseCommand

from server.common import factories
from server.common.models import GoldenFiducials, Fiducials

from process import affine, dicom_import
from process.affine import apply_affine
from process.reports import generate_cube, generate_report
from process.file_io import load_points


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

        johns_hopkins = factories.InstitutionFactory.create(
            name='Johns Hopkins',
            address='3101 Wyman Park Dr.\nBaltimore, MD 21211',
            phone_number='555-555-5555',
        )

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
        machine_c = factories.MachineFactory.create(
            name='MRI Scanner North',
            institution=johns_hopkins,
        )


        cad_fiducials_603A = load_points('data/points/603A.mat')['points']
        phantom_model_603A = factories.PhantomModelFactory(
            name='CIRS 603A',
            model_number='603A',
            cad_fiducials__fiducials=cad_fiducials_603A,
        )

        # TODO: use real 604 cad fiducials
        phantom_model_604 = factories.PhantomModelFactory(
            name='CIRS 604',
            model_number='604',
        )

        phantom_a = factories.PhantomFactory(
            name='Head Phantom 1',
            model=phantom_model_603A,
            serial_number='A123',
        )
        phantom_b = factories.PhantomFactory(
            name='Head Phantom 2',
            model=phantom_model_603A,
            serial_number='B123',
        )
        phantom_c = factories.PhantomFactory(
            name='Body Phantom',
            model=phantom_model_604,
            serial_number='C123',
        )
        phantom_d = factories.PhantomFactory(
            name='Head Phantom 1',
            model=phantom_model_603A,
            serial_number='A123',
            institution=johns_hopkins,
        )
        phantom_e = factories.PhantomFactory(
            name='Head Phantom 2',
            model=phantom_model_603A,
            serial_number='B123',
            institution=johns_hopkins,
        )
        phantom_f = factories.PhantomFactory(
            name='Body Phantom',
            model=phantom_model_604,
            serial_number='C123',
            institution=johns_hopkins,
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

        machine_sequence_pair_a = factories.MachineSequencePairFactory(
            machine=machine_a,
            sequence=sequence_a,
            tolerance=2.25
        )
        machine_sequence_pair_b = factories.MachineSequencePairFactory(
            machine=machine_a,
            sequence=sequence_b,
        )
        machine_sequence_pair_c = factories.MachineSequencePairFactory(
            machine=machine_b,
            sequence=sequence_a,
        )
        machine_sequence_pair_d = factories.MachineSequencePairFactory(
            machine=machine_c,
            sequence=sequence_a,
        )
        machine_sequence_pair_e = factories.MachineSequencePairFactory(
            machine=machine_c,
            sequence=sequence_c,
        )

        ct_dicom_files = os.path.join(settings.BASE_DIR, 'data/dicom/001_ct_603A_E3148_ST1.25.zip')
        dicom_series_ct = factories.DicomSeriesFactory()

        with open(ct_dicom_files, 'rb') as f:
            dicom_series_ct.zipped_dicom_files.save(f'{uuid.uuid4()}.zip', f)

        golden_fiducials_a = factories.GoldenFiducialsFactory(
            phantom=phantom_d,
            dicom_series=dicom_series_ct,
            type=GoldenFiducials.CT,
        )
        golden_fiducials_b = factories.GoldenFiducialsFactory(
            phantom=phantom_d,
            type=GoldenFiducials.CSV,
        )

        mri_dicom_files = os.path.join(settings.BASE_DIR, 'data/dicom/006_mri_603A_UVA_Axial_2ME2SRS5.zip')
        dicom_series_mri = factories.DicomSeriesFactory()

        with open(mri_dicom_files, 'rb') as f:
            dicom_series_mri.zipped_dicom_files.save(f'{uuid.uuid4()}.zip', f)

        with zipfile.ZipFile(mri_dicom_files, 'r') as zip_file:
            datasets = dicom_import.dicom_datasets_from_zip(zip_file)
        voxels, ijk_to_xyz = dicom_import.combine_slices(datasets)

        # TODO: replace this with real datasets
        for i in range(3):
            A = generate_cube(2, 4)
            B = generate_cube(2, 4)

            error = randint(6, 10)
            affine_matrix = affine.translation_rotation(0, 0, 0, np.pi / 180 * error, np.pi / 180 * error, np.pi / 180 * error)

            A = apply_affine(affine_matrix, A)

            scan = factories.ScanFactory(
                creator=manager,
                machine_sequence_pair=machine_sequence_pair_a,
                detected_fiducials=factories.FiducialsFactory(fiducials=A),
                TP_A_S=factories.FiducialsFactory(fiducials=A),
                TP_B=factories.FiducialsFactory(fiducials=B),
                dicom_series=dicom_series_mri,
                tolerance=2.25,
            )

            report_filename = f'{uuid.uuid4()}.pdf'
            report_path = os.path.join(settings.BASE_DIR, 'tmp', report_filename)
            generate_report(
                A,
                B,
                datasets,
                voxels,
                ijk_to_xyz,
                '603A',
                scan.tolerance,
                johns_hopkins,
                report_path
            )

            with open(report_path, 'rb') as report_file:
                scan.full_report.save(report_filename, File(report_file))

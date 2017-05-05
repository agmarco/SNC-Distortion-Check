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
from server.common.tasks import process_scan

from process import affine, dicom_import
from process.affine import apply_affine
from process.reports import generate_cube, generate_reports
from process.file_io import load_points


class Command(BaseCommand):
    help = 'Load the demo data into the database.'

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
            name='Head Phantom With Various Gold Standards',
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

        self.generate_gold_standard_points_demo(phantom_d)
        self.generate_scan_progression_demo(manager, machine_a, sequence_a, 9)
        self.generate_real_reports_demo(manager, machine_a, sequence_b)

    def generate_gold_standard_points_demo(self, phantom):
        '''
        Attach several types of gold standard points to a particular phantom to
        demonstate the various types of uploads we have available.
        '''
        ct_dicom_files = os.path.join(settings.BASE_DIR, 'data/dicom/001_ct_603A_E3148_ST1.25.zip')
        dicom_series_ct = factories.DicomSeriesFactory()

        with open(ct_dicom_files, 'rb') as f:
            dicom_series_ct.zipped_dicom_files.save(f'{uuid.uuid4()}.zip', f)

        # TODO: make this have real CT-based fiducials
        factories.GoldenFiducialsFactory(
            phantom=phantom,
            dicom_series=dicom_series_ct,
            type=GoldenFiducials.CT,
        )

        # TODO: make this have real CSV-based fiducials
        factories.GoldenFiducialsFactory(
            phantom=phantom,
            type=GoldenFiducials.CSV,
        )

    def generate_real_reports_demo(self, creator, machine, sequence):
        '''
        Run the process scan task so that we have real pdf reports to
        demonstrate.
        '''
        machine_sequence = factories.MachineSequencePairFactory(
            machine=machine,
            sequence=sequence,
        )

        # the factories default to the 006 data set
        scan = factories.ScanFactory(
            creator=creator,
            machine_sequence_pair=machine_sequence,
            tolerance=2.25,
        )
        process_scan(scan.pk)

    def generate_scan_progression_demo(self, creator, machine, sequence, sequence_length):
        '''
        Create a MachineSequencePair that demonstrates our nice SVG graph.

        NOTE: the pdf reports will all be invalid.
        '''
        machine_sequence = factories.MachineSequencePairFactory(
            machine=machine,
            sequence=sequence,
            tolerance=2.25
        )

        for i in range(sequence_length):
            A = generate_cube(2, 4)
            B = generate_cube(2, 4)

            random_angle = randint(6, 10)*np.pi/180
            affine_matrix = affine.translation_rotation(0, 0, 0, random_angle, random_angle, random_angle)

            A = apply_affine(affine_matrix, A)

            scan = factories.ScanFactory(
                creator=creator,
                machine_sequence_pair=machine_sequence,
                detected_fiducials=factories.FiducialsFactory(fiducials=A),
                TP_A_S=factories.FiducialsFactory(fiducials=A),
                TP_B=factories.FiducialsFactory(fiducials=B),
                tolerance=machine_sequence.tolerance,
                processing=False,
            )

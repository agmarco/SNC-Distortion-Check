import os
import uuid
from random import randint

import numpy as np

from django.conf import settings
from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand
from django.core.files import File

from server.common import factories
from server.common.models import GoldenFiducials, create_scan
from server.common.tasks import process_scan

from process import affine
from process.affine import apply_affine
from process.reports import generate_cube
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
            email="admin@cirsinc.com",
            first_name="admin",
            last_name="cirs",
            is_staff=True,
            is_superuser=True,
        )

        demo_institution = factories.InstitutionFactory.create(
            name='Demo Institution',
            address='Demo Institution\n12345 Happy Drive\nBaltimore, MD 21211',
            phone_number='555-555-5555',
        )

        manager = factories.UserFactory.create(
            first_name="Edsger",
            last_name="Dijkstra",
            email="manager@cirsinc.com",
            institution=demo_institution,
            groups=[managers],
        )

        medical_physicist = factories.UserFactory.create(
            first_name="Mary",
            last_name="Jane",
            email="physicist@cirsinc.com",
            institution=demo_institution,
            groups=[medical_physicists],
        )

        therapist = factories.UserFactory.create(
            first_name="John",
            last_name="Doe",
            email="therapist@cirsinc.com",
            institution=demo_institution,
            groups=[therapists],
        )

        machine_a = factories.MachineFactory.create(
            name='MRI Scanner Example Scan Sequence',
            institution=demo_institution,
        )
        machine_b = factories.MachineFactory.create(
            name='MRI Scanner Example Full PDF Reports',
            institution=demo_institution,
        )
        machine_c = factories.MachineFactory.create(
            name='MRI Scanner North',
            institution=demo_institution,
        )


        cad_fiducials_603A = load_points('data/points/603A.mat')['points']
        phantom_model_603A = factories.PhantomModelFactory(
            name='CIRS 603A',
            model_number='603A',
            cad_fiducials__fiducials=cad_fiducials_603A,
        )

        cad_fiducials_604 = load_points('data/points/604.mat')['points']
        phantom_model_604 = factories.PhantomModelFactory(
            name='CIRS 604',
            model_number='604',
            cad_fiducials__fiducials=cad_fiducials_604,
        )

        cad_fiducials_604_GS = load_points('data/points/604-GS.mat')['points']
        phantom_model_604_GS = factories.PhantomModelFactory(
            name='CIRS 604-GS',
            model_number='604-GS',
            cad_fiducials__fiducials=cad_fiducials_604_GS,
        )

        cad_fiducials_603A_GS = load_points('data/points/603-GS.mat')['points']
        phantom_model_603A_GS = factories.PhantomModelFactory(
            name='CIRS 603-GS',
            model_number='603-GS',
            cad_fiducials__fiducials=cad_fiducials_603A_GS,
        )

        phantom_a = factories.PhantomFactory(
            name='Head Phantom With Various Gold Standards',
            model=phantom_model_603A,
            institution=demo_institution,
        )
        phantom_b = factories.PhantomFactory(
            name='Head Phantom 2',
            model=phantom_model_603A,
            institution=demo_institution,
        )
        phantom_c = factories.PhantomFactory(
            name='Body Phantom',
            model=phantom_model_604,
            institution=demo_institution,
        )
        phantom_d = factories.PhantomFactory(
            name='Body Phantom (GS)',
            model=phantom_model_604_GS,
            institution=demo_institution,
        )
        phantom_e = factories.PhantomFactory(
            name='Head Phantom (GS)',
            model=phantom_model_603A_GS,
            institution=demo_institution,
        )

        # lots of test phantoms
        for _ in range(20):
            factories.PhantomFactory(
                name='Head Phantom',
                model=phantom_model_603A,
            )

        for _ in range(20):
            factories.PhantomFactory(
                name='Body Phantom',
                model=phantom_model_604,
            )

        for _ in range(20):
            factories.PhantomFactory(
                name='Body Phantom (GS)',
                model=phantom_model_604_GS,
            )

        for _ in range(20):
            factories.PhantomFactory(
                name='Head Phantom (GS)',
                model=phantom_model_603A_GS,
            )

        sequence_a = factories.SequenceFactory(
            name="T1-Weighted Abdominal",
            institution=demo_institution,
        )
        sequence_b = factories.SequenceFactory(
            name="T1-Weighted Neural",
            institution=demo_institution,
        )
        sequence_c = factories.SequenceFactory(
            name="T2-Weighted Neural",
            institution=demo_institution,
        )

        self.generate_gold_standard_points_demo(phantom_a)
        self.generate_scan_progression_demo(manager, machine_a, sequence_a, 9)

    def generate_gold_standard_points_demo(self, phantom):
        '''
        Attach several types of gold standard points to a particular phantom to
        demonstrate the various types of uploads we have available.
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
            affine_matrix = affine.rotation_translation(0, 0, 0, random_angle, random_angle, random_angle)

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

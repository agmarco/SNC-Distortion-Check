import os
import io
import zipfile
import uuid

import scipy.io
from django.conf import settings
from rest_framework.renderers import JSONRenderer

from process.file_io import save_voxels
from . import serializers


# TODO write MAT files in memory?
def dump_raw_data(scan):
    voxels_path = os.path.join(settings.BASE_DIR, f'tmp/{uuid.uuid4()}.mat')
    voxels_data = {
        'phantom_model': scan.phantom.model.model_number,
        'modality': 'mri',
        'voxels': scan.dicom_series.voxels,
    }
    save_voxels(voxels_path, voxels_data)

    raw_points_path = os.path.join(settings.BASE_DIR, f'tmp/{uuid.uuid4()}.mat')
    raw_points_data = {
        'all': scan.detected_fiducials.fiducials,
        'TP': scan.TP_B.fiducials,
    }
    scipy.io.savemat(raw_points_path, raw_points_data)

    renderer = JSONRenderer()

    phantom = serializers.PhantomSerializer(scan.phantom)
    phantom_s = io.BytesIO()
    phantom_s.write(renderer.render(phantom.data))

    machine = serializers.MachineSerializer(scan.machine_sequence_pair.machine)
    machine_s = io.BytesIO()
    machine_s.write(renderer.render(machine.data))

    sequence = serializers.SequenceSerializer(scan.machine_sequence_pair.sequence)
    sequence_s = io.BytesIO()
    sequence_s.write(renderer.render(sequence.data))

    institution = serializers.InstitutionSerializer(scan.institution)
    institution_s = io.BytesIO()
    institution_s.write(renderer.render(institution.data))

    files = {
        'dicom.zip': scan.dicom_series.zipped_dicom_files.path,
        'voxels.mat': voxels_path,
        'raw_points.mat': raw_points_path,
    }

    streams = {
        'phantom.json': phantom_s,
        'machine.json': machine_s,
        'sequence.json': sequence_s,
        'institution.json': institution_s,
    }

    s = io.BytesIO()
    with zipfile.ZipFile(s, 'w', zipfile.ZIP_DEFLATED) as zf:
        for zip_path, path in files.items():
            zf.write(path, zip_path)

        for zip_path, stream in streams.items():
            zf.writestr(zip_path, stream.getvalue())

    return s

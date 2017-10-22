import zipfile
import uuid
import os
import io

import scipy.io
from django.conf import settings
from rest_framework.renderers import JSONRenderer


def dump_raw_scan_data(scan):
    voxels_path = os.path.join(settings.BASE_DIR, f'tmp/{uuid.uuid4()}.mat')
    voxels_data = {
        'phantom_model': scan.phantom.model.model_number,
        'modality': 'mri',
        'voxels': scan.dicom_series.voxels,
    }
    save_voxels(voxels_path, voxels_data)

    fiducials_path = os.path.join(settings.BASE_DIR, f'tmp/{uuid.uuid4()}.mat')
    fiducials_data = {
        'all_golden_fiducials_unregistered'] = scan.golden_fiducials.fiducials.fiducials,
    }
    if scan.detected_fiducials:
        fiducials_data['all_detected_fiducials'] = scan.detected_fiducials.fiducials
    if scan.TP_A_S:
        fiducials_data['matched_golden_fiducials_registered'] = scan.TP_A_S.fiducials
    if scan.TP_B:
        fiducials_data['matched_detected_fiducials'] = scan.TP_B.fiducials
    scipy.io.savemat(fiducials_path, fiducials_data)

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
        'voxels.mat': voxels_path,
        'fiducials.mat': fiducials_path,
    }

    streams = {
        'phantom.json': phantom_s,
        'machine.json': machine_s,
        'sequence.json': sequence_s,
        'institution.json': institution_s,
    }

    zipped_dicom_files = scan.dicom_series.zipped_dicom_files
    zipped_dicom_files.seek(0)  # rewind the file, as it may have been read earlier

    s = io.BytesIO()
    with zipfile.ZipFile(s, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('dicom.zip', zipped_dicom_files.read())

        for zip_path, path in files.items():
            zf.write(path, zip_path)

        for zip_path, stream in streams.items():
            zf.writestr(zip_path, stream.getvalue())

    return s

import zipfile
import uuid
import os
import io

import scipy.io
from django.conf import settings
from rest_framework.renderers import JSONRenderer

from process.file_io import save_voxels
from . import serializers

def dump_raw_scan_data(scan):
    '''
    Dump as much useful intermediate data about a scan into a zipfile as
    possible.  This should work even if the scan failed part of the way
    through.

    Currently, the zipfile is constructed in memory.
    '''
    files = {}
    streams = {}

    phantom_data = serializers.PhantomSerializer(scan.phantom).data
    streams['phantom.json'] = jsonify_into_bytes(phantom_data)
    machine_data = serializers.MachineSerializer(scan.machine_sequence_pair.machine).data
    streams['machine.json'] = jsonify_into_bytes(machine_data)
    sequence_data = serializers.SequenceSerializer(scan.machine_sequence_pair.sequence).data
    streams['sequence.json'] = jsonify_into_bytes(sequence_data)
    institution_data = serializers.InstitutionSerializer(scan.institution).data
    streams['institution.json'] = jsonify_into_bytes(institution_data)

    if scan.dicom_series:
        zipped_dicom_files = scan.dicom_series.zipped_dicom_files
        zipped_dicom_files.seek(0)  # rewind the file, as it may have been read earlier
        streams['dicom.zip'] = io.BytesIO(zipped_dicom_files.read())

        voxels_path = generate_tempory_file_path('.mat')
        voxels_data = {
            'phantom_model': scan.phantom.model.model_number,
            'modality': 'mri',
            'voxels': scan.dicom_series.voxels,
        }
        save_voxels(voxels_path, voxels_data)
        files['voxels.mat'] = voxels_path

    fiducials_data = collect_fiducial_data(scan)
    if fiducials_data:
        fiducials_path = generate_tempory_file_path('.mat')
        scipy.io.savemat(fiducials_path, fiducials_data)
        files['fiducials.mat'] = fiducials_path

    raw_scan_data_zipped = zip_in_memory(files, streams)
    return raw_scan_data_zipped


def collect_fiducial_data(scan):
    fiducials_data = {
        'all_golden_fiducials_unregistered': scan.golden_fiducials.fiducials.fiducials,
    }
    if scan.detected_fiducials:
        fiducials_data['all_detected_fiducials'] = scan.detected_fiducials.fiducials
    if scan.TP_A_S:
        fiducials_data['matched_golden_fiducials_registered'] = scan.TP_A_S.fiducials
    if scan.TP_B:
        fiducials_data['matched_detected_fiducials'] = scan.TP_B.fiducials
    return fiducials_data


def generate_tempory_file_path(extension):
    return os.path.join(settings.BASE_DIR, f'tmp/{uuid.uuid4()}{extension}')


def jsonify_into_bytes(data):
    renderer = JSONRenderer()
    byte_stream = io.BytesIO()
    byte_stream.write(renderer.render(data))
    return byte_stream


def zip_in_memory(files, streams):
    zipped_bytes = io.BytesIO()
    with zipfile.ZipFile(zipped_bytes, 'w', zipfile.ZIP_DEFLATED) as zf:
        for zip_path, path in files.items():
            zf.write(path, zip_path)

        for zip_path, stream in streams.items():
            zf.writestr(zip_path, stream.getvalue())
    return zipped_bytes

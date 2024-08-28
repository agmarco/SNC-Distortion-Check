import { Action } from 'redux-actions';
import { call, all, takeLatest } from 'redux-saga/effects';

import * as constants from './constants';
import { uploadToS3 } from 'common/sagas';

export function* uploadScanToS3(action: Action<File>): any {
    yield call(uploadToS3, action.payload, 'uploadScan.dicom_archive.0', 'uploadScan.dicom_archive_url');
}

function* uploadScan(): any {
    yield takeLatest(constants.UPLOAD_SCAN_TO_S3, uploadScanToS3);
}

export default function* () {
    yield all([
        uploadScan(),
    ]);
};

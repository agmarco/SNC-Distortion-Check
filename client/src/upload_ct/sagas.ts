import { Action } from 'redux-actions';
import { call, all, takeLatest } from 'redux-saga/effects';

import * as constants from './constants';
import { uploadToS3 } from 'common/sagas';

export function* uploadCtToS3(action: Action<File>): any {
    yield call(uploadToS3, action.payload, 'uploadCt.dicom_archive.0', 'uploadCt.dicom_archive_url');
}

function* uploadCt(): any {
    yield takeLatest(constants.UPLOAD_CT_TO_S3, uploadCtToS3);
}

export default function* () {
    yield all([
        uploadCt(),
    ]);
};

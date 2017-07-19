import { Action } from 'redux-actions';
import { call, put, all, takeLatest } from 'redux-saga/effects';
import { actions as formActions } from 'react-redux-form';

import * as constants from './constants';
import * as actions from './actions';
import * as api from 'common/api';

export function* uploadScanToS3(action: Action<actions.IUploadScanToS3Payload>): any {
    const errorMsg = `Your file could not be uploaded. Please try again,
            or contact CIRS support if this problem persists.`;

    yield put(formActions.setPending('uploadScan', true));

    const getS3UrlResponse = yield api.signS3((action.payload as actions.IUploadScanToS3Payload).file);

    if (getS3UrlResponse.ok) {
        const s3Data = yield call(getS3UrlResponse.json.bind(getS3UrlResponse));

        const postData = new FormData();
        Object.keys(s3Data.data.fields).forEach(key => postData.append(key, s3Data.data.fields[key]));
        postData.append('file', (action.payload as actions.IUploadScanToS3Payload).file);

        const uploadToS3Response = yield api.uploadToS3(s3Data.data.url, postData);

        if (uploadToS3Response.ok) {
            yield put(formActions.change('uploadScan.dicom_archive_url', s3Data.url));
            yield put(formActions.setSubmitted('uploadScan', true));
            (document.getElementById(
                (action.payload as actions.IUploadScanToS3Payload).formId) as HTMLFormElement
            ).submit();
        } else {
            yield put(formActions.setPending('uploadScan', false));
            yield put(formActions.setErrors('uploadScan.__all__', errorMsg));
            yield put(formActions.setTouched(`uploadScan.__all__`));
        }

    } else {
        yield put(formActions.setPending('uploadScan', false));
        yield put(formActions.setErrors('uploadScan.__all__', errorMsg));

        // TODO: this shouldn't be necessary
        // Will probably fix itself when we can properly set global errors on the form model itself
        yield put(formActions.setTouched(`uploadScan.__all__`));
    }
}

function* uploadScan(): any {
    yield takeLatest(constants.UPLOAD_SCAN_TO_S3, uploadScanToS3);
}

export default function* () {
    yield all([
        uploadScan(),
    ]);
};

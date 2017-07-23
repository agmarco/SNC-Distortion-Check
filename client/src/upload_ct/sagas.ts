import { Action } from 'redux-actions';
import { call, put, all, takeLatest } from 'redux-saga/effects';
import { actions as formActions } from 'react-redux-form';

import * as constants from './constants';
import * as api from 'common/api';

export function* uploadCtToS3(action: Action<File>): any {
    const file = (action.payload as File);
    const errorMsg = `Your file could not be uploaded. Please try again,
            or contact CIRS support if this problem persists.`;

    yield put(formActions.setPending('uploadCt.dicom_archive.0', true));
    const getS3UrlResponse = yield api.signS3(file);

    if (getS3UrlResponse.ok) {
        const s3Data = yield call(getS3UrlResponse.json.bind(getS3UrlResponse));

        const postData = new FormData();
        Object.keys(s3Data.data.fields).forEach(key => postData.append(key, s3Data.data.fields[key]));
        postData.append('file', file);

        const uploadToS3Response = yield api.uploadToS3(s3Data.data.url, postData);

        if (uploadToS3Response.ok) {
            yield put(formActions.change('uploadCt.dicom_archive_url', s3Data.url));
            yield put(formActions.setPending('uploadCt.dicom_archive.0', false));
        } else {
            yield put(formActions.setPending('uploadCt.dicom_archive.0', false));
            yield put(formActions.setErrors('uploadCt.__all__', errorMsg));
            yield put(formActions.setTouched(`uploadCt.__all__`));
        }

    } else {
        yield put(formActions.setPending('uploadCt.dicom_archive.0', false));
        yield put(formActions.setErrors('uploadCt.__all__', errorMsg));
        yield put(formActions.setTouched(`uploadCt.__all__`));
    }
}

function* uploadCt(): any {
    yield takeLatest(constants.UPLOAD_CT_TO_S3, uploadCtToS3);
}

export default function* () {
    yield all([
        uploadCt(),
    ]);
};

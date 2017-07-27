import { call, put } from 'redux-saga/effects';
import { actions as formActions } from 'react-redux-form';

import * as api from './api';

function* displayError(model: string, msg: string) {
    yield put(formActions.setPending(model, false));
    yield put(formActions.setErrors(model, msg));
    yield put(formActions.setTouched(model));
}

export function* uploadToS3(file: File, fileModel: string, urlModel: string): any {
    const errorMsg = `Your file could not be uploaded. Please try again,
            or contact CIRS support if this problem persists.`;

    yield put(formActions.setPending(fileModel, true));
    const signS3Response = yield call(api.signS3, file);

    if (signS3Response.ok) {
        const s3Data = yield call(signS3Response.json.bind(signS3Response));

        const postData = new FormData();
        Object.keys(s3Data.data.fields).forEach(key => postData.append(key, s3Data.data.fields[key]));
        postData.append('file', file);

        const uploadToS3Response = yield call(api.uploadToS3, s3Data.data.url, postData);

        if (uploadToS3Response.ok) {
            yield put(formActions.change(urlModel, s3Data.url));
            yield put(formActions.setPending(fileModel, false));
        } else {
            yield call(displayError, fileModel, errorMsg);
        }

    } else {
        yield call(displayError, fileModel, errorMsg);
    }
}

import { call, put } from 'redux-saga/effects';
import { actions as formActions } from 'react-redux-form';

import { addOkCheck } from 'common/api';
import * as api from './api';

export function* uploadToS3(file: File, fileModel: string, urlModel: string): any {
    const errorMsg = `Your file could not be uploaded. Please try again,
            or contact CIRS support if this problem persists.`;

    yield put(formActions.setPending(fileModel, true));
    try {
        const signS3Response = yield call(addOkCheck(api.signS3), file);
        const s3Data = yield call(signS3Response.json.bind(signS3Response));

        const postData = new FormData();
        Object.keys(s3Data.data.fields).forEach(key => postData.append(key, s3Data.data.fields[key]));
        postData.append('file', file);

        yield call(addOkCheck(api.uploadToS3), s3Data.data.url, postData);
        yield put(formActions.change(urlModel, s3Data.url));
    } catch (error) {
        yield put(formActions.setErrors(fileModel, errorMsg));
        yield put(formActions.setTouched(fileModel));
    } finally {
        yield put(formActions.setPending(fileModel, false));
    }
}

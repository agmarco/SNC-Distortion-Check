import * as Cookies from 'js-cookie';
import { call } from 'redux-saga/effects';

declare const SIGN_S3_URL: string;

export const signS3 = (file: File) => {
    return call(fetch, `${SIGN_S3_URL}?file_name=${file.name}&file_type=${file.type}`, {
        method: 'GET',
        credentials: 'same-origin',
        headers: {
            'X-CSRFToken': Cookies.get('csrftoken'),
        },
    });
};

export const uploadToS3 = (url: string, body: FormData) => {
    return call(fetch, url, {
        method: 'POST',
        headers: {
            'Content-Type': 'multipart/form-data',
        },
        body,
    });
};

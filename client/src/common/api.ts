import * as Cookies from 'js-cookie';
import { delay } from 'redux-saga';
import { call, race, CallEffect } from 'redux-saga/effects';

import { encode } from 'common/utils';

declare const VALIDATE_SERIAL_URL: string;
declare const SIGN_S3_URL: string;

export function addTimeout(apiOuter: CallEffect) {
    return call(function* (api: CallEffect) {
        const {response} = yield race({
            response: api,
            timeout: call(delay, 5000),
        });

        if (response) {
            return response;
        } else {
            throw new Error("Request timeout");
        }
    }, apiOuter);
}

export function addOkCheck(apiOuter: CallEffect) {
    return call(function* (api: CallEffect) {
        const response = yield api;

        if (response.ok) {
            return response;
        } else {
            throw new Error(response.statusText);
        }
    }, apiOuter);
}

export const validateSerial = (body: any) => {
    return call(fetch, VALIDATE_SERIAL_URL, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': Cookies.get('csrftoken'),
        },
        body: encode(body),
    });
};

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

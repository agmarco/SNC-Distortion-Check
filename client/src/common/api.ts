import * as Cookies from 'js-cookie';
import { delay } from 'redux-saga';
import { call, race, CallEffect } from 'redux-saga/effects';

import { encode } from 'common/utils';

declare const VALIDATE_SERIAL_URL: string;

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

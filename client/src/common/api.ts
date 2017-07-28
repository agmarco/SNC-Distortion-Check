import * as Cookies from 'js-cookie';
import { delay } from 'redux-saga';
import { call, race, CallEffectFn, CallEffect } from 'redux-saga/effects';

import { encode } from 'common/utils';

declare const VALIDATE_SERIAL_URL: string;
declare const SIGN_S3_URL: string;

type UniversalFunc<T> = (...args: T[]) => any;

interface IUniversalCallEffectFactory<R> {
  <T>(fn: CallEffectFn<UniversalFunc<T>>, ...args: T[]): R;
}

type UniversalCallEffectFactory = IUniversalCallEffectFactory<CallEffect>;

// TODO: handle network errors as well (via a try/catch with fetch)

export function addTimeout(api: (...args: any[]) => Promise<Response> | IterableIterator<any>) {
    return function* (...args: any[]) {
        const { response } = yield race({
            response: (call as UniversalCallEffectFactory)(api, ...args),
            timeout: call(delay, 5000),
        });

        if (response) {
            return response;
        } else {
            throw new Error("Request timeout");
        }
    };
}

export function addOkCheck(api: (...args: any[]) => Promise<Response> | IterableIterator<any>) {
    return function* (...args: any[]) {
        const response = yield (call as UniversalCallEffectFactory)(api, ...args);

        if (response.ok) {
            return response;
        } else {
            throw new Error(response.statusText);
        }
    };
}

export const validateSerial = (body: any) => {
    return fetch(VALIDATE_SERIAL_URL, {
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
    return fetch(`${SIGN_S3_URL}?file_name=${file.name}&file_type=${file.type}`, {
        method: 'GET',
        credentials: 'same-origin',
        headers: {
            'X-CSRFToken': Cookies.get('csrftoken'),
        },
    });
};

export const uploadToS3 = (url: string, body: FormData) => {
    return fetch(url, {
        method: 'POST',
        body,
    });
};

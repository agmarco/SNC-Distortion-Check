import * as Cookies from 'js-cookie';
import { call } from 'redux-saga/effects';

import { encode } from 'common/utils';


declare const VALIDATE_SERIAL_URL: string;


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

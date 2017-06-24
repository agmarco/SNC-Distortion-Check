import * as Cookies from 'js-cookie';
import { delay } from 'redux-saga';
import { call, race, CallEffect } from 'redux-saga/effects';

import { IMachineSequencePairDto } from 'common/service';


declare const MACHINE_SEQUENCE_PAIR: IMachineSequencePairDto;
declare const POLL_SCANS_URL: string;


function* addTimeout(api: CallEffect) {
    const {response} = yield race({
        response: api,
        timeout: call(delay, 5000),
    });

    if (response) {
        return response;
    } else {
        throw new Error("Request timeout");
    }
}


function* addOkCheck(api: CallEffect) {
    const response = yield api;

    if (response.ok) {
        return response;
    } else {
        throw new Error(response.statusText);
    }
}


export default class Api {
    static pollScans(body: any) {
        return call(addOkCheck, call(addTimeout, call(fetch, POLL_SCANS_URL, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': Cookies.get('csrftoken'),
            },
            body: JSON.stringify(body),
        })));
    }
}

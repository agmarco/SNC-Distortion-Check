import * as Cookies from 'js-cookie';
import { call } from 'redux-saga/effects';

import { encode } from 'common/utils';
import { IMachineSequencePairDto } from 'common/service';


declare const MACHINE_SEQUENCE_PAIR: IMachineSequencePairDto;
declare const POLL_SCANS_URL: string;
declare const UPDATE_TOLERANCE_URL: string;


export const pollScans = (body: any) => {
    return call(fetch, POLL_SCANS_URL, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': Cookies.get('csrftoken'),
        },
        body: JSON.stringify(body),
    });
};


export const updateTolerance = (body: any) => {
    return call(fetch, UPDATE_TOLERANCE_URL, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': Cookies.get('csrftoken'),
        },
        body: encode(body),
    });
};

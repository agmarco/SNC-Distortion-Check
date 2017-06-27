import * as Cookies from 'js-cookie';
import { call } from 'redux-saga/effects';

import { addTimeout, addOkCheck } from 'common/api';
import { IMachineSequencePairDto } from 'common/service';


declare const MACHINE_SEQUENCE_PAIR: IMachineSequencePairDto;
declare const POLL_SCANS_URL: string;


export default class Api {
    static pollScans(body: any) {
        return call(fetch, POLL_SCANS_URL, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': Cookies.get('csrftoken'),
            },
            body: JSON.stringify(body),
        });
    }
}

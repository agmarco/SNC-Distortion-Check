import * as Cookies from 'js-cookie';
import { call } from 'redux-saga/effects';

import { IMachineSequencePairDto } from 'common/service';


declare const MACHINE_SEQUENCE_PAIR: IMachineSequencePairDto;
declare const POLL_CT_URL: string;


export const pollCt = (body: any) => {
    return call(fetch, POLL_CT_URL, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': Cookies.get('csrftoken'),
        },
        body: JSON.stringify(body),
    });
};

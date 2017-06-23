import * as Cookies from 'js-cookie';
import { Action } from 'redux-actions';
import { delay } from 'redux-saga';
import { call, put, all, select, takeLatest } from 'redux-saga/effects';
import { actions as formActions } from 'react-redux-form';

import { IScanDto, IMachineSequencePairDto } from 'common/service';
import { encode } from 'common/utils';
import * as constants from './constants';
import * as actions from './actions';
import * as selectors from './selectors';


export declare const MACHINE_SEQUENCE_PAIR: IMachineSequencePairDto;
export declare const POLL_SCANS_URL: string;
export declare const UPDATE_TOLERANCE_URL: string;


function* pollScans(): any {
    while (true) {
        yield call(delay, 10000);
        const scans = (yield select(selectors.getScans)) as IScanDto[];
        const unprocessedScans = scans.filter(s => s.processing);

        if (unprocessedScans.length === 0) {
            break;
        } else {
            const response = yield call(fetch, POLL_SCANS_URL, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': Cookies.get('csrftoken'),
                },
                body: JSON.stringify({
                    machine_sequence_pair_pk: MACHINE_SEQUENCE_PAIR.pk,
                    scan_pks: unprocessedScans.map(s => s.pk),
                }),
            });

            if (response.ok) {
                const updatedScans = (yield call(response.json.bind(response))) as IScanDto[];
                for (const scan of updatedScans) {
                    yield put(actions.updateScan(scan));
                }
            }
        }
    }
}


function* fetchUpdateTolerance(action: Action<actions.IUpdateTolerancePayload>): any {
    if (action.payload) {
        yield put(formActions.setPending('forms.tolerance', true));

        const response = yield call(fetch, UPDATE_TOLERANCE_URL, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': Cookies.get('csrftoken'),
            },
            body: encode({pk: action.payload.pk, tolerance: action.payload.tolerance}),
        });

        yield put(formActions.setPending('forms.tolerance', false));

        if (response.ok) {
            yield put(actions.updateToleranceSuccess(true));
        } else {
            yield put(actions.updateToleranceSuccess(false));
        }
    }
}


function* updateTolerance(): any {
    yield takeLatest(constants.UPDATE_TOLERANCE, fetchUpdateTolerance);
}


export default function* () {
    yield all([
        pollScans(),
        updateTolerance(),
    ]);
};

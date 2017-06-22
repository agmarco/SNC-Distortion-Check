import * as Cookies from 'js-cookie';
import { delay } from 'redux-saga';
import { call, put, all, select, fork, take, cancel } from 'redux-saga/effects';
import { actions as formActions } from 'react-redux-form';

import { IMachineSequencePairDto, IScanDto } from 'common/service';
import { encode } from 'common/utils';
import * as constants from './constants';
import * as actions from './actions';
import * as selectors from './selectors';

declare const MACHINE_SEQUENCE_PAIR: IMachineSequencePairDto;
declare const POLL_SCANS_URL: string;
declare const UPDATE_TOLERANCE_URL: string;

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

function* fetchUpdateTolerance({ pk, tolerance }: actions.IUpdateTolerancePayload): any {
    yield put(formActions.setPending('forms.tolerance', true));

    const response = yield call(fetch, UPDATE_TOLERANCE_URL, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': Cookies.get('csrftoken'),
        },
        body: encode({pk, tolerance}),
    });

    yield put(formActions.setPending('forms.tolerance', false));
    if (response.ok) {
        yield put(actions.updateToleranceSuccess(true));
    } else {
        yield put(actions.updateToleranceSuccess(false));
    }
}

function* updateTolerance(): any {
    let fetchUpdateToleranceTask;

    while (true) {
        const updateToleranceAction = yield take(constants.UPDATE_TOLERANCE);
        if (fetchUpdateToleranceTask) {
            yield cancel(fetchUpdateToleranceTask);
        }
        fetchUpdateToleranceTask = yield fork(fetchUpdateTolerance, updateToleranceAction.payload);
    }
}

export default function* () {
    yield all([
        pollScans(),
        updateTolerance(),
    ]);
};

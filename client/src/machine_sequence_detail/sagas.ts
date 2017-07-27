import { Action } from 'redux-actions';
import { delay } from 'redux-saga';
import { call, put, all, select, takeLatest } from 'redux-saga/effects';
import { actions as formActions } from 'react-redux-form';

import { IMachineSequencePairDto, IScanDto } from 'common/service';
import { addOkCheck, addTimeout } from 'common/api';
import * as constants from './constants';
import * as actions from './actions';
import * as selectors from './selectors';
import * as api from './api';

declare const MACHINE_SEQUENCE_PAIR: IMachineSequencePairDto;

export function* pollScans(): any {
    while (true) {
        yield call(delay, 10000);
        const scans = (yield select(selectors.getScans)) as IScanDto[];
        const unprocessedScans = scans.filter(s => s.processing);

        if (unprocessedScans.length === 0) {
            break;
        } else {
            try {
                const response = yield call(addOkCheck(addTimeout(api.pollScans)), {
                    machine_sequence_pair_pk: MACHINE_SEQUENCE_PAIR.pk,
                    scan_pks: unprocessedScans.map(s => s.pk),
                });
                const updatedScans = yield call(response.json.bind(response));
                for (const scan of updatedScans) {
                    yield put(actions.updateScan(scan));
                }
            } catch (error) {
                yield put(actions.pollScansFailure(error.message));
                break;
            }
        }
    }
}

function* fetchUpdateTolerance(action: Action<actions.IUpdateTolerancePayload>): any {
    if (action.payload) {
        yield put(formActions.setPending('forms.tolerance', true));
        const response = yield call(api.updateTolerance, {pk: action.payload.pk, tolerance: action.payload.tolerance});
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

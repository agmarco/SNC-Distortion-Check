import { Action } from 'redux-actions';
import { delay } from 'redux-saga';
import { call, put, all, select, takeLatest } from 'redux-saga/effects';
import { actions as formActions } from 'react-redux-form';

import { IScanDto } from 'common/service';
import { addOkCheck, addTimeout } from 'common/api';
import * as constants from './constants';
import * as actions from './actions';
import * as selectors from './selectors';
import * as api from './api';

export function* pollScans(): any {
    while (true) {
        yield call(delay, 10000);
        const scans = (yield select(selectors.getScans)) as IScanDto[];
        const unprocessedScans = scans.filter(s => s.processing);

        if (unprocessedScans.length === 0) {
            break;
        } else {
            try {
                const response = yield call(addTimeout(addOkCheck(api.pollScans)), {
                    machine_sequence_pair_pk: window.MACHINE_SEQUENCE_PAIR.pk,
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
        try {
            yield call(addOkCheck(api.updateTolerance), {
                pk: action.payload.pk,
                tolerance: action.payload.tolerance,
            });
            yield put(actions.updateToleranceSuccess(true));
        } catch (error) {
            yield put(actions.updateToleranceSuccess(false));
        } finally {
            yield put(formActions.setPending('forms.tolerance', false));
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

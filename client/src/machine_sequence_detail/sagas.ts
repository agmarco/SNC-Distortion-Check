import { delay } from 'redux-saga';
import { call, put, all, select } from 'redux-saga/effects';

import { IMachineSequencePairDto, IScanDto } from 'common/service';
import { addOkCheck, addTimeout } from 'common/api';
import * as actions from './actions';
import * as selectors from './selectors';
import Api from './api';

declare const MACHINE_SEQUENCE_PAIR: IMachineSequencePairDto;

export function* pollScans(): any {
    while (true) {
        yield call(delay, 10000);
        const scans = (yield select(selectors.getScans)) as IScanDto[];

        if (scans.every(s => !s.processing)) {
            break;
        } else {
            const unprocessedScans = scans.filter(s => s.processing);
            try {
                const response = yield addOkCheck(addTimeout(Api.pollScans({
                    machine_sequence_pair_pk: MACHINE_SEQUENCE_PAIR.pk,
                    scan_pks: unprocessedScans.map(s => s.pk),
                })));
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

export default function* () {
    yield all([
        pollScans(),
    ]);
};

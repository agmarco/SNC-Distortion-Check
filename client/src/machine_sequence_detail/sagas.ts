import * as Cookies from 'js-cookie';
import { delay } from 'redux-saga';
import { call, put, all, select } from 'redux-saga/effects';

import { IMachineSequencePairDto, IScanDto } from 'common/service';
import * as actions from './actions';
import * as selectors from './selectors';

declare const MACHINE_SEQUENCE_PAIR: IMachineSequencePairDto;
declare const POLL_SCANS_URL: string;

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
            const updatedScans = yield call(response.json.bind(response));
            for (const scan of updatedScans) {
                yield put(actions.updateScan(scan));
            }
        }
    }
}

export default function* () {
    yield all([
        pollScans(),
    ]);
};

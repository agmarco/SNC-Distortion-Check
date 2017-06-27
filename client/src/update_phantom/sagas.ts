import { delay } from 'redux-saga';
import { call, put, all, select } from 'redux-saga/effects';

import { IGoldenFiducialsDto, IPhantomDto } from 'common/service';
import { addOkCheck, addTimeout } from 'common/api';
import * as actions from './actions';
import * as selectors from './selectors';
import Api from './api';


declare const PHANTOM: IPhantomDto;
declare const POLL_CT_URL: string;


function* pollCt(): any {
    while (true) {
        yield call(delay, 10000);
        const goldenFiducialsSet = (yield select(selectors.getGoldenFiducialsSet)) as IGoldenFiducialsDto[];
        const unprocessedGoldenFiducialsSet = goldenFiducialsSet.filter(s => s.processing);

        if (unprocessedGoldenFiducialsSet.length === 0) {
            break;
        } else {
            try {
                const response = yield addOkCheck(addTimeout(Api.pollCt({
                    phantom_pk: PHANTOM.pk,
                    golden_fiducials_pks: unprocessedGoldenFiducialsSet.map(g => g.pk),
                })));
                const updatedGoldenFiducialsSet = yield call(response.json.bind(response));
                for (const goldenFiducials of updatedGoldenFiducialsSet) {
                    yield put(actions.updateGoldenFiducials(goldenFiducials));
                }
            } catch (error) {
                yield put(actions.pollCtFailure(error.message));
            }
        }
    }
}


export default function* () {
    yield all([
        pollCt(),
    ]);
};

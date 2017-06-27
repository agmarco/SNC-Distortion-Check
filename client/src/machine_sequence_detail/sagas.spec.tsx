import { put } from 'redux-saga/effects';
import { assert } from 'chai';

import { scanFixture } from 'common/fixtures';
import * as sagas from './sagas';
import * as actions from './actions';

// describe('pollScans', () => {
//     it('should throw error', () => {
//         const scans = [
//             scanFixture(undefined, {processing: true}),
//         ];
//
//         const iterator = sagas.pollScans();
//
//         iterator.next();
//         iterator.next();
//         iterator.next(scans);
//
//         const error = {message: ''};
//         assert.deepEqual(
//             iterator.throw(error).value,
//             put(actions.pollScansFailure(error.message)),
//         );
//     });
// });

import { combineReducers } from 'redux';
import { handleActions } from 'redux-actions';
import { combineForms, FormState } from 'react-redux-form';

import { IScanDto } from 'common/service';
import * as constants from './constants';

declare const SCANS: IScanDto[];

export interface IAppState {
    scans: IScanDto[];
    pollScansError: string | null;
    forms: {
        forms: {
            tolerance: FormState;
        };
        tolerance: { tolerance: number; };
    };
}

const scanReducer = handleActions<IScanDto[], any>({
    [constants.UPDATE_SCAN]: (state, action) => state.map((scan) => {
      if (scan.pk === action.payload.pk) {
          return action.payload;
      } else {
          return scan;
      }
    }),
}, SCANS);

const pollScansErrorReducer = handleActions<string | null, any>({
    [constants.POLL_SCANS_FAILURE]: (state, action) => action.payload,
}, null);

export default combineReducers({
    scans: scanReducer,
    pollScansError: pollScansErrorReducer,
    forms: combineForms({
        tolerance: {tolerance: ''},
    }, 'forms'),
});

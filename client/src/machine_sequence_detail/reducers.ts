import { combineReducers } from 'redux';
import { handleActions } from 'redux-actions';
import { combineForms, FormState } from 'react-redux-form';

import { IScanDto, IMachineSequencePairDto } from 'common/service';
import * as constants from './constants';

declare const SCANS: IScanDto[];
declare const MACHINE_SEQUENCE_PAIR: IMachineSequencePairDto;

export interface IAppState {
    scans: IScanDto[];
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

export default combineReducers({
    scans: scanReducer,
    forms: combineForms({
        tolerance: {tolerance: MACHINE_SEQUENCE_PAIR.tolerance},
    }, 'forms'),
});

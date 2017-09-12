import { combineReducers } from 'redux';
import { handleActions } from 'redux-actions';
import { combineForms } from 'react-redux-form';

import { IScanDto, IMachineSequencePairDto } from 'common/service';
import { CirsFormState } from 'common/forms';
import { IToleranceForm } from './forms';
import * as constants from './constants';

declare const MACHINE_SEQUENCE_PAIR: IMachineSequencePairDto;
declare const SCANS: IScanDto[];

export interface IAppState {
    scans: IScanDto[];
    pollScansError: string | null;
    updateToleranceSuccess: boolean | null;
    forms: CirsFormState<IFormModelState>;
}

interface IFormModelState {
    tolerance: IToleranceForm;
}

const scanReducer = handleActions<IScanDto[], any>({
    [constants.UPDATE_SCAN]: (state, action) => state.map((scan) => {
      if (scan.pk === action.payload.pk) {
          return action.payload;
      } else {
          return scan;
      }
    }),
    [constants.FILTER_SCANS]: (state, action) => {
        return SCANS.filter(s => action.payload === "all" || s.phantom.pk === Number(action.payload));
    },
}, SCANS);

const pollScansErrorReducer = handleActions<string | null, any>({
    [constants.POLL_SCANS_FAILURE]: (state, action) => action.payload,
}, null);

const updateToleranceSuccessReducer = handleActions<boolean | null, any>({
    [constants.UPDATE_TOLERANCE_SUCCESS]: (state, action) => action.payload,
}, null);

export default combineReducers({
    scans: scanReducer,
    pollScansError: pollScansErrorReducer,
    updateToleranceSuccess: updateToleranceSuccessReducer,
    forms: combineForms({
        tolerance: {tolerance: MACHINE_SEQUENCE_PAIR.tolerance},
    }, 'forms'),
});

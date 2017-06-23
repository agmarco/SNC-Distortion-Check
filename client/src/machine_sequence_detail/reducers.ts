import { combineReducers } from 'redux';
import { handleActions } from 'redux-actions';
import { combineForms } from 'react-redux-form';

import { IScanDto, IMachineSequencePairDto } from 'common/service';
import { CirsFormState } from 'common/forms';
import { IToleranceForm } from './forms';
import * as constants from './constants';


export declare const MACHINE_SEQUENCE_PAIR: IMachineSequencePairDto;
export declare const SCANS: IScanDto[];


export interface IAppState {
    scans: IScanDto[];
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
}, SCANS);


const updateToleranceSuccessReducer = handleActions<boolean | null, any>({
    [constants.UPDATE_TOLERANCE_SUCCESS]: (state, action) => action.payload,
}, null);


export default combineReducers({
    scans: scanReducer,
    updateToleranceSuccess: updateToleranceSuccessReducer,
    forms: combineForms({
        tolerance: {tolerance: MACHINE_SEQUENCE_PAIR.tolerance},
    }, 'forms'),
});

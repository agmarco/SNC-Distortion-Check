import { combineReducers } from 'redux';
import { handleActions } from 'redux-actions';
import { combineForms } from 'react-redux-form';

import { IGoldenFiducialsDto } from 'common/service';
import { CirsFormState } from 'common/forms';
import { IUpdatePhantomForm } from './forms';
import * as constants from './constants';


export declare const FORM_INITIAL: IUpdatePhantomForm;
export declare const GOLDEN_FIDUCIALS_SET: IGoldenFiducialsDto[];


export interface IAppState {
    goldenFiducialsSet: IGoldenFiducialsDto[];
    forms: CirsFormState<IFormModelState>;
}


interface IFormModelState {
    phantom: IUpdatePhantomForm;
}


const goldenFiducialsSetReducer = handleActions<IGoldenFiducialsDto[], any>({
    [constants.UPDATE_GOLDEN_FIDUCIALS]: (state, action) => state.map((goldenFiducials) => {
      if (goldenFiducials.pk === action.payload.pk) {
          return action.payload;
      } else {
          return goldenFiducials;
      }
    }),
}, GOLDEN_FIDUCIALS_SET);


export default combineReducers({
    goldenFiducialsSet: goldenFiducialsSetReducer,
    forms: combineForms({
        phantom: FORM_INITIAL,
    }, 'forms'),
});

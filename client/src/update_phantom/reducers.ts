import { combineReducers } from 'redux';
import { handleActions } from 'redux-actions';
import { combineForms, FormState } from 'react-redux-form';

import { IGoldenFiducialsDto } from 'common/service';
import * as constants from './constants';
import { IUpdatePhantomForm } from './forms';

declare const GOLDEN_FIDUCIALS_SET: IGoldenFiducialsDto[];
declare const FORM_INITIAL: IUpdatePhantomForm;

export interface IAppState {
    goldenFiducialsSet: IGoldenFiducialsDto[];
    forms: {
        forms: {
            phantom: FormState;
        };
        phantom: IUpdatePhantomForm;
    };
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

import { createAction } from 'redux-actions';

import { IGoldenFiducialsDto } from 'common/service';
import * as constants from './constants';


export const updateGoldenFiducials = createAction<IGoldenFiducialsDto>(constants.UPDATE_GOLDEN_FIDUCIALS);


export const pollCtFailure = createAction<string>(constants.POLL_CT_FAILURE);

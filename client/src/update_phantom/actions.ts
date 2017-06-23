import { createAction } from 'redux-actions';

import { IGoldenFiducialsDto } from 'common/service';
import * as constants from './constants';


export const updateGoldenFiducials = createAction<IGoldenFiducialsDto>(constants.UPDATE_GOLDEN_FIDUCIALS);

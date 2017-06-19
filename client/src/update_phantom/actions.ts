import { createAction } from 'redux-actions';

import { IGoldenFiducialsDto } from 'common/service';
import * as constants from './constants';

export interface IUpdateGoldenFiducialsPayload {
    goldenFiducials: IGoldenFiducialsDto;
}

export const updateGoldenFiducials = createAction<IUpdateGoldenFiducialsPayload>(constants.UPDATE_GOLDEN_FIDUCIALS);

import { createAction } from 'redux-actions';

import { IScanDto } from 'common/service';
import * as constants from './constants';

export const updateScan = createAction<IScanDto>(constants.UPDATE_SCAN);

export interface IUpdateTolerancePayload {
    pk: number;
    tolerance: number;
}
export const updateTolerance = createAction<IUpdateTolerancePayload>(constants.UPDATE_TOLERANCE);

export const updateToleranceSuccess = createAction<boolean | null>(constants.UPDATE_TOLERANCE_SUCCESS);

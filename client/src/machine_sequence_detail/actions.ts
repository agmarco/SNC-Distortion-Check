import { createAction } from 'redux-actions';

import { IScanDto } from 'common/service';
import * as constants from './constants';

export interface IUpdateScanPayload {
    scan: IScanDto;
}

export const updateScan = createAction<IUpdateScanPayload>(constants.UPDATE_SCAN);
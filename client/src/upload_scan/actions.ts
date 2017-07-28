import { createAction } from 'redux-actions';

import * as constants from './constants';

export const uploadScanToS3 = createAction<File>(constants.UPLOAD_SCAN_TO_S3);

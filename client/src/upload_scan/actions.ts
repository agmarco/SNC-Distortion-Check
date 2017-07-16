import { createAction } from 'redux-actions';

import * as constants from './constants';

export interface IUploadScanToS3Payload {
    file: File;
    formId: string;
}

export const uploadScanToS3 = createAction<IUploadScanToS3Payload>(constants.UPLOAD_SCAN_TO_S3);

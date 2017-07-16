import { createAction } from 'redux-actions';

import * as constants from './constants';

export interface IUploadCtToS3Payload {
    file: File;
    formId: string;
}

export const uploadCtToS3 = createAction<IUploadCtToS3Payload>(constants.UPLOAD_CT_TO_S3);

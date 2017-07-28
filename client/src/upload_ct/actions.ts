import { createAction } from 'redux-actions';

import * as constants from './constants';

export const uploadCtToS3 = createAction<File>(constants.UPLOAD_CT_TO_S3);

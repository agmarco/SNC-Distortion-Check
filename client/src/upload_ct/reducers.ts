import { combineForms } from 'react-redux-form';

import { IUploadCtForm } from './forms';

declare const FORM_INITIAL: IUploadCtForm;

export default combineForms({
    uploadCt: FORM_INITIAL,
});

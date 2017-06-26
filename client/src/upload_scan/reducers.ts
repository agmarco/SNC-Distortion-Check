import { combineForms } from 'react-redux-form';

import { IUploadScanForm } from './forms';


declare const FORM_INITIAL: IUploadScanForm;


export default combineForms({
    uploadScan: FORM_INITIAL,
});

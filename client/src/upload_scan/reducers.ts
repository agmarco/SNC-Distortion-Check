import { combineForms } from 'react-redux-form';

import { IUploadScanForm } from './forms';


export declare const FORM_INITIAL: IUploadScanForm;


export default combineForms({
    uploadScan: FORM_INITIAL,
});

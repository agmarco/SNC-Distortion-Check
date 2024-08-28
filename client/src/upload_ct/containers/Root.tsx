import React from 'react';

import { IDjangoFormErrors } from 'common/forms';
import UploadCtForm from '../components/UploadCtForm';

declare const CANCEL_URL: string;
declare const FORM_ACTION: string;
declare const FORM_ERRORS: IDjangoFormErrors;

export default () => (
    <div>
        <h1>Upload Gold Standard CT</h1>
        <UploadCtForm
            cancelUrl={CANCEL_URL}
            formAction={FORM_ACTION}
            formErrors={FORM_ERRORS}
        />
    </div>
);

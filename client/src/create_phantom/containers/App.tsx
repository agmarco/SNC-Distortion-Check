import React from 'react';

import { IFormErrors } from 'common/forms';
import AddPhantomForm from '../components/AddPhantomForm';

declare const VALIDATE_SERIAL_URL: string;
declare const CANCEL_URL: string;
declare const FORM_ERRORS: IFormErrors;

export default () => (
    <div>
        <h1>Add Phantom</h1>
        <AddPhantomForm
            validateSerialUrl={VALIDATE_SERIAL_URL}
            cancelUrl={CANCEL_URL}
            formErrors={FORM_ERRORS}
        />
    </div>
);

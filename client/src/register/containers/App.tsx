import React from 'react';

import { IDjangoFormErrors } from 'common/forms';
import RegisterForm from '../components/RegisterForm';

declare const VALIDATE_SERIAL_URL: string;
declare const CANCEL_URL: string;
declare const FORM_ERRORS: IDjangoFormErrors;

export default () => (
    <div>
        <h1>Register New Account</h1>
        <RegisterForm
            validateSerialUrl={VALIDATE_SERIAL_URL}
            cancelUrl={CANCEL_URL}
            formErrors={FORM_ERRORS}
        />
    </div>
);

import React from 'react';

import { IDjangoFormErrors } from 'common/forms';
import RegisterForm from '../components/RegisterForm';


declare const CANCEL_URL: string;
declare const FORM_ACTION: string;
declare const FORM_ERRORS: IDjangoFormErrors;


export default () => (
    <div>
        <h1>Register New Account</h1>
        <RegisterForm
            cancelUrl={CANCEL_URL}
            formAction={FORM_ACTION}
            formErrors={FORM_ERRORS}
        />
    </div>
);

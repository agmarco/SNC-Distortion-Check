import React from 'react';

import { IDjangoFormErrors } from 'common/forms';
import CreatePhantomForm from '../components/CreatePhantomForm';
import { ICreatePhantomForm } from '../forms';

declare const VALIDATE_SERIAL_URL: string;
declare const CANCEL_URL: string;
declare const FORM_ACTION: string;
declare const FORM_INITIAL: ICreatePhantomForm | null;
declare const FORM_ERRORS: IDjangoFormErrors;

export default () => (
    <div>
        <h1>Add Phantom</h1>
        <CreatePhantomForm
            validateSerialUrl={VALIDATE_SERIAL_URL}
            cancelUrl={CANCEL_URL}
            formErrors={FORM_ERRORS}
            formAction={FORM_ACTION}
        />
    </div>
);

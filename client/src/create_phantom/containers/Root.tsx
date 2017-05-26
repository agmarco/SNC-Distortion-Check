import React from 'react';

import { IDjangoErrors } from 'common/forms';
import CreatePhantomForm from '../components/CreatePhantomForm';

declare const VALIDATE_SERIAL_URL: string;
declare const CANCEL_URL: string;
declare const FORM_ACTION: string;
declare const FORM_DATA: IPhantomForm | null;
declare const FORM_ERRORS: IDjangoErrors;

interface IPhantomForm {
    name: string;
    serial_number: string;
}

export default () => (
    <div>
        <h1>Add Phantom</h1>
        <CreatePhantomForm
            validateSerialUrl={VALIDATE_SERIAL_URL}
            cancelUrl={CANCEL_URL}
            djangoData={FORM_DATA}
            djangoErrors={FORM_ERRORS}
            formAction={FORM_ACTION}
        />
    </div>
);

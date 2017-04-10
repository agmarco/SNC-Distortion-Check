import * as React from 'react';

import AddPhantomForm from '../components/AddPhantomForm';

declare const CREATE_PHANTOM_URL: string;
declare const VALIDATE_SERIAL_URL: string;
declare const CANCEL_URL: string;
declare const FORM_ERRORS: {[field: string]: string[]};

export default () => (
    <div>
        <h1>Add Phantom</h1>
        <AddPhantomForm
            createPhantomUrl={CREATE_PHANTOM_URL}
            validateSerialUrl={VALIDATE_SERIAL_URL}
            cancelUrl={CANCEL_URL}
            formErrors={FORM_ERRORS}
        />
    </div>
);

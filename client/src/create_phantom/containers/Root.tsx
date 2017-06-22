import React from 'react';

import { IDjangoFormErrors } from 'common/forms';
import CreatePhantomForm from '../components/CreatePhantomForm';

declare const CANCEL_URL: string;
declare const FORM_ACTION: string;
declare const FORM_ERRORS: IDjangoFormErrors;

export default () => (
    <div>
        <h1>Add Phantom</h1>
        <CreatePhantomForm
            cancelUrl={CANCEL_URL}
            formAction={FORM_ACTION}
            formErrors={FORM_ERRORS}
        />
    </div>
);

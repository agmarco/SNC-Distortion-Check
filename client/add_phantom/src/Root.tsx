import * as React from 'react';
import * as Cookies from 'js-cookie';

import AddPhantomForm from './components/AddPhantomForm';

declare const CREATE_PHANTOM_URL: string;
declare const VALIDATE_SERIAL_URL: string;
declare const CANCEL_URL: string;
declare const FORM_ERRORS: {[field: string]: string[]};

export default () => (
    <AddPhantomForm
        create_phantom_url={CREATE_PHANTOM_URL}
        validate_serial_url={VALIDATE_SERIAL_URL}
        cancel_url={CANCEL_URL}
        form_errors={FORM_ERRORS}
        csrftoken={Cookies.get('csrftoken')}
    />
);

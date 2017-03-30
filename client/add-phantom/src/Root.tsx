import * as React from 'react';
import * as Cookies from 'js-cookie';
import { AppContainer } from 'react-hot-loader';

import AddPhantomForm from './AddPhantomForm';

export default () => (
    <AppContainer>
        <AddPhantomForm
            create_phantom_url={__CREATE_PHANTOM_URL__}
            validate_serial_url={__VALIDATE_SERIAL_URL__}
            cancel_url={__CANCEL_URL__}
            csrftoken={Cookies.get('csrftoken')}
        />
    </AppContainer>
);

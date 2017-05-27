import React from 'react';
import { createStore } from 'redux';
import { Provider } from 'react-redux';
import { combineForms } from 'react-redux-form';

import Root from './Root';
import { IUploadScanForm } from '../forms';

declare const FORM_INITIAL: IUploadScanForm;

const store = createStore(combineForms({
    uploadScan: FORM_INITIAL,
}));

export default () => (
    <Provider store={store}>
        <Root />
    </Provider>
);

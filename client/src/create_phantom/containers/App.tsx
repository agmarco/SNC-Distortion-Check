import React from 'react';
import { createStore } from 'redux';
import { Provider } from 'react-redux';
import { combineForms } from 'react-redux-form';

import Root from './Root';
import { ICreatePhantomForm } from '../forms';

declare const FORM_INITIAL: ICreatePhantomForm;

const store = createStore(combineForms({
    phantom: FORM_INITIAL,
}));

export default () => (
    <Provider store={store}>
        <Root />
    </Provider>
);

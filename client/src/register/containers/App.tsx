import React from 'react';
import { createStore } from 'redux';
import { Provider } from 'react-redux';
import { combineForms } from 'react-redux-form';

import Root from './Root';
import { IRegisterForm } from '../forms';

declare const FORM_INITIAL: IRegisterForm;

const store = createStore(combineForms({
    register: FORM_INITIAL,
}));

export default () => (
    <Provider store={store}>
        <Root />
    </Provider>
);

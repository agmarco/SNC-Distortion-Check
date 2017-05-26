import React from 'react';
import { createStore } from 'redux';
import { Provider } from 'react-redux';
import { combineForms } from 'react-redux-form';

import Root from './Root';

declare const FORM_DATA: IPhantomForm | null;

interface IPhantomForm {
    name: string;
    serial_number: string;
}

const initialPhantom = FORM_DATA || {
    name: '',
    serial_number: '',
};

const store = createStore(combineForms({
    phantom: initialPhantom,
}));

export default () => (
    <Provider store={store}>
        <Root />
    </Provider>
);

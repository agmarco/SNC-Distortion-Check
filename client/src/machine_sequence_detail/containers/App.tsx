import React from 'react';
import { createStore } from 'redux';
import { Provider } from 'react-redux';
import { combineForms } from 'react-redux-form';

import Root from './Root';

const store = createStore(combineForms({
    tolerance: { tolerance: '' },
}));

export default () => (
    <Provider store={store}>
        <Root />
    </Provider>
);

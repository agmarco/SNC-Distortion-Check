import React from 'react';
import { Provider } from 'react-redux';

import Root from './Root';
import configureStore from '../store';

import './App.scss';

const store = configureStore();


export default () => (
    <Provider store={store}>
        <Root />
    </Provider>
);

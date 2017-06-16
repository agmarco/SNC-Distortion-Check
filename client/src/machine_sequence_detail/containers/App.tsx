import React from 'react';
import { createStore, applyMiddleware } from 'redux';
import { Provider } from 'react-redux';
import createSagaMiddleware from 'redux-saga';

import Root from './Root';
import reducer from '../reducers';
import saga from '../sagas';

const sagaMiddleware = createSagaMiddleware();
const store = createStore(reducer, applyMiddleware(sagaMiddleware));

sagaMiddleware.run(saga);

export default () => (
    <Provider store={store}>
        <Root />
    </Provider>
);

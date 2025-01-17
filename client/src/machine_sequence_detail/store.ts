import { createStore, applyMiddleware } from 'redux';
import createSagaMiddleware from 'redux-saga';

import rootReducer from './reducers';
import rootSaga from './sagas';

export default () => {
    const sagaMiddleware = createSagaMiddleware();
    const store = createStore(rootReducer, applyMiddleware(sagaMiddleware));
    sagaMiddleware.run(rootSaga);

    if (module.hot) {
        module.hot.accept('./reducers', () => {
            const nextRootReducer = (require('./reducers') as any).default;
            store.replaceReducer(nextRootReducer);
        });
    }

    return store;
};

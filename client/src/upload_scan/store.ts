import { createStore } from 'redux';

import rootReducer from './reducers';


export default () => {
    const store = createStore(rootReducer);

    if (module.hot) {
        module.hot.accept('./reducers', () => {
            const nextRootReducer = require('./reducers').default;
            store.replaceReducer(nextRootReducer);
        });
    }

    return store;
};

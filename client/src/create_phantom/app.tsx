import { renderApp } from 'common/utils';
import App from './containers/App';

import 'base/app.scss';

renderApp(App, 'create-phantom-app');

// Hot Module Replacement API
if (module.hot) {
    module.hot.accept('./containers/App', () => {
        renderApp(App, 'create-phantom-app');
    });
}
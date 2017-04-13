import { renderApp } from 'common/utils';
import App from './containers/App';

import 'base/app.scss';

renderApp(App, 'landing-app');

// Hot Module Replacement API
if (module.hot) {
    module.hot.accept('./containers/App', () => {
        renderApp(App, 'landing-app');
    });
}

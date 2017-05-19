import { renderApp } from 'common/utils';
import App from './containers/App';

renderApp(App, 'register-app');

// Hot Module Replacement API
if (module.hot) {
    module.hot.accept('./containers/App', () => {
        renderApp(App, 'register-app');
    });
}

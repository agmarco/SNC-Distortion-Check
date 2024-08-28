import { renderApp } from 'common/utils';
import App from './containers/App';

renderApp(App, 'update-phantom-app');

// Hot Module Replacement API
if (module.hot) {
    module.hot.accept('./containers/App', () => {
        renderApp(App, 'update-phantom-app');
    });
}

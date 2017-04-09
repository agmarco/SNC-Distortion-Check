import 'd3';

import { renderApp } from 'common/utils';
import App from './containers/App';
import './box.js';

renderApp(App, 'machine-sequence-detail-app');

// Hot Module Replacement API
if (module.hot) {
    module.hot.accept('./containers/App', () => {
        renderApp(App, 'machine-sequence-detail-app');
    });
}

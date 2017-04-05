import * as React from 'react';
import * as ReactDOM from 'react-dom';
import { AppContainer } from 'react-hot-loader';

import Root from './Root';

ReactDOM.render(<Root />, document.getElementById('machine-sequence-detail-app'));

// TODO HMR only works first time

if (module.hot) {
    module.hot.accept('Root', () => {
        require('Root');
        ReactDOM.render(<AppContainer><Root /></AppContainer>, document.getElementById('machine-sequence-detail-app'));
    });
}

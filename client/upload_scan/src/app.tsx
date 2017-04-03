import * as React from 'react';
import * as ReactDOM from 'react-dom';
import { AppContainer } from 'react-hot-loader';

import Root from './Root';

ReactDOM.render(<Root />, document.getElementById('upload-scan-app'));

if (module.hot) {
    module.hot.accept('Root', () => {
        require('Root');
        ReactDOM.render(<AppContainer><Root /></AppContainer>, document.getElementById('upload-scan-app'));
    });
}

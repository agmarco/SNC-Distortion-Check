import * as React from 'react';
import * as ReactDOM from 'react-dom';

import Root from './Root';

ReactDOM.render(<Root />, document.getElementById('machine_sequences-app'));

if (module.hot) {
    module.hot.accept('Root', () => {
        require('Root');
        ReactDOM.render(<Root />, document.getElementById('machine_sequences-app'));
    });
}

import * as React from 'react';
import * as ReactDOM from 'react-dom';

import Root from './Root';

ReactDOM.render(<Root />, document.getElementById('add-phantom-app'));

if (module.hot) {
    module.hot.accept('Root', () => {
        require('Root');
        ReactDOM.render(<Root />, document.getElementById('add-phantom-app'));
    });
}

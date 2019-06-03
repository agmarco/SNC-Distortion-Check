import { renderApp } from 'common/utils';
import { IScanDto, IMachineSequencePairDto } from 'common/service';
import App from './containers/App';

interface Window {
    MACHINE_SEQUENCE_PAIR: IMachineSequencePairDto;
    SCANS: IScanDto[];
}

renderApp(App, 'machine-sequence-detail-app');

// Hot Module Replacement API
if (module.hot) {
    module.hot.accept('./containers/App', () => {
        renderApp(App, 'machine-sequence-detail-app');
    });
}

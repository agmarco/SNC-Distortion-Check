import * as React from 'react';

import { AppContainer } from 'react-hot-loader';

import MachineSequenceTable from './MachineSequenceTable';

export default class extends React.Component<{}, {}> {
    render() {
        return (
            <AppContainer>
                <MachineSequenceTable
                    machineSequencePairs={__MACHINE_SEQUENCE_PAIRS__}
                    machines={__MACHINES__}
                    sequences={__SEQUENCES__}
                />
            </AppContainer>
        );
    }
}

import * as React from 'react';
import { AppContainer } from 'react-hot-loader';

import { MachineSequencePairDTO } from 'common/service';
import ScanTable from './components/ScanTable';

declare const MACHINE_SEQUENCE_PAIR: MachineSequencePairDTO;

// TODO all tables should have the action links split into multiple columns
// TODO golden fiducials processing row
// TODO where should AppContainer go?

export default () => (
    <AppContainer>
        <ScanTable
            machineSequencePair={MACHINE_SEQUENCE_PAIR}
        />
    </AppContainer>
);

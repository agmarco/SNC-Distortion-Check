import * as React from 'react';
import { AppContainer } from 'react-hot-loader';

import { MachineSequenceTable, MachineSequencePair, Machine, Sequence } from 'cirs-common';

declare const __MACHINE_SEQUENCE_PAIRS__: MachineSequencePair[];
declare const __MACHINES__: Machine[];
declare const __SEQUENCES__: Sequence[];

export default () => (
    <AppContainer>
        <MachineSequenceTable
            machineSequencePairs={__MACHINE_SEQUENCE_PAIRS__}
            machines={__MACHINES__}
            sequences={__SEQUENCES__}
        />
    </AppContainer>
);

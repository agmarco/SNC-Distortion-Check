import * as React from 'react';
import { AppContainer } from 'react-hot-loader';
import { MachineSequenceTable, MachineSequencePair, Machine, Sequence } from 'cirs-common';

// it would be better to put this in a globals.d.ts, but we need to import the interfaces from cirs-common, which
// automatically makes the file a module
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

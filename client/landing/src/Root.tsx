import * as React from 'react';
import { AppContainer } from 'react-hot-loader';

import { MachineSequenceTable } from 'common/components';
import { MachineSequencePairDTO, MachineDTO, SequenceDTO } from 'common/service';

declare const __MACHINE_SEQUENCE_PAIRS__: MachineSequencePairDTO[];
declare const __MACHINES__: MachineDTO[];
declare const __SEQUENCES__: SequenceDTO[];

export default () => (
    <AppContainer>
        <MachineSequenceTable
            machineSequencePairs={__MACHINE_SEQUENCE_PAIRS__}
            machines={__MACHINES__}
            sequences={__SEQUENCES__}
        />
    </AppContainer>
);

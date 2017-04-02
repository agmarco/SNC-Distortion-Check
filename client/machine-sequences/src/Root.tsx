import * as React from 'react';
import { AppContainer } from 'react-hot-loader';

import { MachineSequenceTable } from 'common/components';
import { MachineSequencePairDTO } from 'common/service';

declare const MACHINE_SEQUENCE_PAIRS: MachineSequencePairDTO[];

export default () => (
    <AppContainer>
        <MachineSequenceTable
            machineSequencePairs={MACHINE_SEQUENCE_PAIRS}
        />
    </AppContainer>
);

import * as React from 'react';
import { AppContainer } from 'react-hot-loader';

import { MachineSequenceTable } from 'common/components';
import { MachineSequencePairDTO, MachineDTO, SequenceDTO } from 'common/service';

declare const __MACHINE_SEQUENCE_PAIRS__: MachineSequencePairDTO[];
declare const __MACHINES__: MachineDTO[];
declare const __SEQUENCES__: SequenceDTO[];
declare const __UPLOAD_SCAN_URL__: string;

export default () => (
    <AppContainer>
        <MachineSequenceTable
            machineSequencePairs={__MACHINE_SEQUENCE_PAIRS__}
            machines={__MACHINES__}
            sequences={__SEQUENCES__}
            upload_scan_url={__UPLOAD_SCAN_URL__}
        />
    </AppContainer>
);

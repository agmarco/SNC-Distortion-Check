import * as React from 'react';
import { AppContainer } from 'react-hot-loader';

import { MachineSequenceTable } from 'common/components';
import { MachineSequencePairDTO } from 'common/service';

declare const MACHINE_SEQUENCE_PAIRS: MachineSequencePairDTO[];
declare const UPLOAD_SCAN_URL: string;

export default () => (
    <AppContainer>
        <MachineSequenceTable
            machineSequencePairs={MACHINE_SEQUENCE_PAIRS}
            upload_scan_url={UPLOAD_SCAN_URL}
        />
    </AppContainer>
);

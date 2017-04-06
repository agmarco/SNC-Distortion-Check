import * as React from 'react';

import { MachineSequenceTable } from 'common/components';
import { IMachineSequencePairDTO } from 'common/service';

declare const MACHINE_SEQUENCE_PAIRS: IMachineSequencePairDTO[];
declare const UPLOAD_SCAN_URL: string;

export default () => (
    <MachineSequenceTable
        machineSequencePairs={MACHINE_SEQUENCE_PAIRS}
        uploadScanUrl={UPLOAD_SCAN_URL}
    />
);

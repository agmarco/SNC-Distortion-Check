import React from 'react';

import { IMachineSequencePairDto } from 'common/service';
import MachineSequenceTable from '../components/MachineSequenceTable';

declare const MACHINE_SEQUENCE_PAIRS: IMachineSequencePairDto[];
declare const UPLOAD_SCAN_URL: string;

// TODO HMR doesn't work with root component
export default () => (
    <div>
        <MachineSequenceTable
            machineSequencePairs={MACHINE_SEQUENCE_PAIRS}
            uploadScanUrl={UPLOAD_SCAN_URL}
        />
    </div>
);

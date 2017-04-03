import * as React from 'react';

import { MachineSequencePairDTO, ScanDTO } from 'common/service';
import ScanTable from './components/ScanTable';

declare const MACHINE_SEQUENCE_PAIR: MachineSequencePairDTO;
declare const SCANS: ScanDTO[];
declare const UPLOAD_SCAN_URL: string;

// TODO all tables should have the action links split into multiple columns
// TODO golden fiducials processing row

export default () => (
    <div>
        <h1>{MACHINE_SEQUENCE_PAIR.machine.name} &mdash; {MACHINE_SEQUENCE_PAIR.sequence.name} Distortion</h1>
        <ScanTable
            scans={SCANS}
            upload_scan_url={UPLOAD_SCAN_URL}
        />
    </div>
);

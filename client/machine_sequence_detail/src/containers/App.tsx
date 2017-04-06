import * as React from 'react';

import { IMachineSequencePairDTO, IScanDTO } from 'common/service';
import ScanChart from 'components/ScanChart';
import ScanTable from 'components/ScanTable';

declare const MACHINE_SEQUENCE_PAIR: IMachineSequencePairDTO;
declare const SCANS: IScanDTO[];
declare const UPLOAD_SCAN_URL: string;

export default () => (
    <div>
        <h1>{MACHINE_SEQUENCE_PAIR.machine.name} &mdash; {MACHINE_SEQUENCE_PAIR.sequence.name} Distortion</h1>
        <h2>Performance over Time</h2>
        <ScanChart
            machineSequencePair={MACHINE_SEQUENCE_PAIR}
            scans={SCANS}
        />
        <h2>Scans</h2>
        <ScanTable
            scans={SCANS}
            uploadScanUrl={UPLOAD_SCAN_URL}
        />
    </div>
);

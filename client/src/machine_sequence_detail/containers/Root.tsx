import React from 'react';

import { IMachineSequencePairDTO, IScanDTO } from 'common/service';
import ScanChart from '../components/ScanChart';
import ScanTable from '../components/ScanTable';
import ToleranceForm from '../components/ToleranceForm';

declare const MACHINE_SEQUENCE_PAIR: IMachineSequencePairDTO;
declare const SCANS: IScanDTO[];
declare const UPLOAD_SCAN_URL: string;
declare const UPDATE_TOLERANCE_URL: string;

interface IRootState {
    tolerance: number;
}

export default class extends React.Component<{}, IRootState> {
    constructor() {
        super();
        this.state = { tolerance: MACHINE_SEQUENCE_PAIR.tolerance };
    }

    handleToleranceChange(event: React.FormEvent<HTMLInputElement>) {
        this.setState({tolerance: (event.target as any).value});
    }

    render() {
        const { tolerance } = this.state;

        return (
            <div>
                <h1>{MACHINE_SEQUENCE_PAIR.machine.name} &mdash; {MACHINE_SEQUENCE_PAIR.sequence.name} Distortion</h1>
                <ToleranceForm
                    updateToleranceUrl={UPDATE_TOLERANCE_URL}
                    machineSequencePair={MACHINE_SEQUENCE_PAIR}
                    tolerance={tolerance}
                    handleToleranceChange={this.handleToleranceChange.bind(this)}
                />
                <h2>Performance over Time</h2>
                <ScanChart
                    machineSequencePair={MACHINE_SEQUENCE_PAIR}
                    tolerance={tolerance}
                    scans={SCANS}
                />
                <h2>Scans</h2>
                <ScanTable
                    scans={SCANS}
                    uploadScanUrl={UPLOAD_SCAN_URL}
                />
            </div>
        );
    }
}

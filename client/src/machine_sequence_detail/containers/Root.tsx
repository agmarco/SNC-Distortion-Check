import React from 'react';
import { Dispatch } from 'redux';
import { connect } from 'react-redux';

import { IMachineSequencePairDto, IScanDto } from 'common/service';
import ScanChart from '../components/ScanChart';
import ScanTable from '../components/ScanTable';
import ToleranceForm from '../components/ToleranceForm';

declare const MACHINE_SEQUENCE_PAIR: IMachineSequencePairDto;
declare const UPLOAD_SCAN_URL: string;

interface IRootProps {
    dispatch?: Dispatch<any>;
    scans?: IScanDto[];
}

interface IRootState {
    tolerance: number;
}

class Root extends React.Component<IRootProps, IRootState> {
    constructor() {
        super();
        this.state = { tolerance: MACHINE_SEQUENCE_PAIR.tolerance };
    }

    handleToleranceChange(event: React.FormEvent<HTMLInputElement>) {
        this.setState({tolerance: (event.target as any).value});
    }

    render() {
        const { scans } = this.props;
        const { tolerance } = this.state;

        return (
            <div>
                <h1>{MACHINE_SEQUENCE_PAIR.machine.name} &mdash; {MACHINE_SEQUENCE_PAIR.sequence.name} Distortion</h1>
                <ToleranceForm
                    machineSequencePair={MACHINE_SEQUENCE_PAIR}
                    tolerance={tolerance}
                    handleToleranceChange={this.handleToleranceChange.bind(this)}
                />
                <h2>Performance over Time</h2>
                <ScanChart
                    machineSequencePair={MACHINE_SEQUENCE_PAIR}
                    tolerance={tolerance}
                    scans={scans as IScanDto[]}
                />
                <h2>Scans</h2>
                <ScanTable
                    scans={scans as IScanDto[]}
                    uploadScanUrl={UPLOAD_SCAN_URL}
                />
            </div>
        );
    }
}

export default connect<any, any, any>((state: any) => ({scans: state.scans}))(Root as any);

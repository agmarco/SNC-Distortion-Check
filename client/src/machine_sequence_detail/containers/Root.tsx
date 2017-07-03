import React from 'react';
import { Dispatch } from 'redux';
import { connect } from 'react-redux';
import isEqual from 'lodash/isEqual';
import uniqueId from 'lodash/uniqueId';

import { IScanDto, IMachineSequencePairDto } from 'common/service';
import ScanChart from '../components/ScanChart';
import ScanTable from '../components/ScanTable';
import ToleranceForm from '../components/ToleranceForm';

declare const MACHINE_SEQUENCE_PAIR: IMachineSequencePairDto;
declare const UPLOAD_SCAN_URL: string;

interface IRootProps {
    dispatch?: Dispatch<any>;
    scans?: IScanDto[];
    pollScansError?: string | null;
}

interface IRootState {
    tolerance: number;
    chartId: string;
}

class Root extends React.Component<IRootProps, IRootState> {
    constructor() {
        super();
        this.state = {tolerance: MACHINE_SEQUENCE_PAIR.tolerance, chartId: uniqueId()};
    }

    handleToleranceChange(event: React.FormEvent<HTMLInputElement>) {
        this.setState({tolerance: (event.target as any).value});
    }

    componentWillReceiveProps(nextProps: IRootProps) {
        if (!isEqual(nextProps.scans, this.props.scans)) {
            // force the component to remount when new data is available
            // ideally, we would update incrementally with d3, but this may require modifying/rewriting box.js
            this.setState({chartId: uniqueId()});
        }
    }

    render() {
        const { scans, pollScansError } = this.props;
        const { tolerance, chartId } = this.state;

        return (
            <div>
                <h1>
                    {MACHINE_SEQUENCE_PAIR.machine.name} &mdash;
                    {MACHINE_SEQUENCE_PAIR.sequence.name} Distortion
                </h1>
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
                    key={chartId}
                />
                <h2>Scans</h2>
                <ScanTable
                    scans={scans as IScanDto[]}
                    uploadScanUrl={UPLOAD_SCAN_URL}
                    pollScansError={pollScansError as string | null}
                />
            </div>
        );
    }
}

export default connect<any, any, any>((state: any) => ({
    scans: state.scans,
    pollScansError: state.pollScansError,
}))(Root as any);

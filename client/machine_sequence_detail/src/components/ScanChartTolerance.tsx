import * as React from 'react';

import { ScanChartProps, ScanChartSettings } from './ScanChart';

export default class extends React.Component<ScanChartProps & ScanChartSettings, {}> {
    render() {
        const { width, machineSequencePair, yScale } = this.props;

        return (
            <line
                className="tolerance"
                x1={0}
                y1={yScale(machineSequencePair.tolerance)}
                x2={width}
                y2={yScale(machineSequencePair.tolerance)}
            />
        );
    }
}

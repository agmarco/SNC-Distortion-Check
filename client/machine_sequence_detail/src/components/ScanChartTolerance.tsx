import * as React from 'react';

import { IScanChartProps, IScanChartSettings } from './ScanChart';

export default class extends React.Component<IScanChartProps & IScanChartSettings, {}> {
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

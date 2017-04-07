import * as React from 'react';

import { IScanChartProps, IScanChartSettings, IZoomable } from './ScanChart';

interface IScanChartToleranceProps extends IScanChartProps, IScanChartSettings, IZoomable {}

export default class extends React.Component<IScanChartToleranceProps, {}> {
    render() {
        const { clipWidth, machineSequencePair, yScale, margin } = this.props;

        return (
            <line
                className="tolerance"
                x1={0}
                y1={yScale(machineSequencePair.tolerance)}
                x2={clipWidth}
                y2={yScale(machineSequencePair.tolerance)}
            />
        );
    }
}

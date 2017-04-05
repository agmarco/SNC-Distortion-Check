import * as React from 'react';

import { ScanChartProps, ScanChartSettings } from './ScanChart';

export default class extends React.Component<ScanChartProps & ScanChartSettings, {}> {
    render() {
        const { margin, height, width, max, machineSequencePair } = this.props;

        return (
            <line
                className="tolerance"
                x1={0}
                y1={height - (machineSequencePair.tolerance / max * height) + margin.top}
                x2={width}
                y2={height - (machineSequencePair.tolerance / max * height) + margin.top}
            />
        );
    }
}

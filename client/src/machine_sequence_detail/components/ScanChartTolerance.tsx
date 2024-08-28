import React from 'react';

import { IScanChartProps, IScanChartSettings, IScrollable } from './ScanChart';

interface IScanChartToleranceProps extends IScanChartProps, IScanChartSettings, IScrollable {}

export default class extends React.Component<IScanChartToleranceProps, {}> {
    render() {
        const { clipWidth, tolerance, yScale } = this.props;

        return (
            <line
                className="tolerance"
                x1={0}
                y1={yScale(tolerance)}
                x2={clipWidth}
                y2={yScale(tolerance)}
            />
        );
    }
}

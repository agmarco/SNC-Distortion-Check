import * as React from 'react';

import { IScanChartProps, IScanChartSettings, IScanData, IScrollable } from './ScanChart';
import Scrollable from './Scrollable';

interface IScanChartAxesProps extends IScanChartProps, IScanChartSettings, IScrollable {}

export default class extends React.Component<IScanChartAxesProps, {}> {
    xAxis: SVGGElement;
    yAxis: SVGGElement;

    componentDidMount() {
        this.renderAxes();
    }

    componentDidUpdate() {
        this.renderAxes();
    }

    renderAxes() {
        const { xScale, yScale, clipWidth, yMin, yMax, data } = this.props;

        d3.select(this.xAxis).call(d3.svg.axis()
            .scale(xScale)
            .orient("bottom")
            .innerTickSize(0)
            .outerTickSize(0)
            .tickPadding(10)
            .tickFormat((pk: number) => {
                const scanData = data.find((d: IScanData) => d[0] === pk);
                return scanData ? scanData.label : pk;
            }));

        d3.select(this.yAxis).call(d3.svg.axis()
            .scale(yScale)
            .orient("left")
            .tickValues(d3.range(yMin, yMax, 0.5))
            .innerTickSize(-clipWidth)
            .outerTickSize(0)
            .tickPadding(10));
    }

    renderXAxis() {
        const { clipWidth, height, margin, scroll } = this.props;

        const xAxisProps = {
            className: "x axis",
            transform: `translate(0, ${height})`,
        };

        const xLabelProps = {
            className: "x-label",
            x: clipWidth / 2,
            y: height + margin.bottom - 16, // 16 is the font size - text is anchored relative to its top
            dy: ".71em",
        };

        return (
            <g>
                <Scrollable {...scroll}>
                    <g ref={(g) => this.xAxis = g} {...xAxisProps} />
                </Scrollable>
                <text {...xLabelProps}>Scans</text>
            </g>
        );
    }

    renderYAxis() {
        const { height, margin } = this.props;

        const yAxisProps = {
            className: "y axis",
        };

        const yLabelProps = {
            className: "y-label",
            x: -height / 2,
            y: -margin.left,
            dy: ".71em",
            transform: "rotate(-90)",
        };

        return (
            <g>
                <g ref={(g) => this.yAxis = g} {...yAxisProps} />
                <text {...yLabelProps}>Distortion (mm)</text>
            </g>
        );
    }

    render() {
        return (
            <g>
                {this.renderXAxis()}
                {this.renderYAxis()}
            </g>
        );
    }
}

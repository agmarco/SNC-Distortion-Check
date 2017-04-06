import * as React from 'react';

import { IScanChartProps, IScanChartSettings, IZoomable } from './ScanChart';

interface IScanChartAxesProps extends IScanChartProps, IScanChartSettings, IZoomable {}

export default class extends React.Component<IScanChartAxesProps, {}> {
    xAxis: SVGGElement;
    yAxis: SVGGElement;

    constructor(props: IScanChartAxesProps) {
        super();
        const { registerZoomHandler, height, clipWidth, width } = props;

        registerZoomHandler((tx: number) => {
            d3.select(this.xAxis).attr('transform', `translate(${clipWidth - width + tx}, ${height})`);
        });
    }

    componentDidMount() {
        this.renderAxes();
    }

    componentDidUpdate() {
        this.renderAxes();
    }

    renderAxes() {
        const { xScale, yScale, width, min, max } = this.props;

        d3.select(this.xAxis).call(d3.svg.axis()
            .scale(xScale)
            .orient("bottom")
            .innerTickSize(0)
            .outerTickSize(0)
            .tickPadding(10));

        d3.select(this.yAxis).call(d3.svg.axis()
            .scale(yScale)
            .orient("left")
            .tickValues(d3.range(min, max, 0.5))
            .innerTickSize(-width)
            .outerTickSize(0)
            .tickPadding(10));
    }

    renderXAxis() {
        const { clipWidth, width, height, margin } = this.props;

        const xAxisProps = {
            className: "x axis",
            transform: `translate(${clipWidth - width}, ${height})`,
        };

        const xLabelProps = {
            className: "x-label",
            x: clipWidth / 2,
            y: height + margin.bottom - 16, // 16 is the font size - text is anchored relative to its top
            dy: ".71em",
        };

        return (
            <g>
                <g ref={(g) => this.xAxis = g}{...xAxisProps} />
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

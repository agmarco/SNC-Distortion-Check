import * as React from 'react';

import { IScanChartProps, IScanChartSettings, IZoomable, IScanData } from './ScanChart';

interface IScanChartAxesProps extends IScanChartProps, IScanChartSettings, IZoomable {}

export default class extends React.Component<IScanChartAxesProps, {}> {
    xAxis: SVGGElement;
    yAxis: SVGGElement;

    constructor(props: IScanChartAxesProps) {
        super();
        const { registerZoomHandler, clipHeight, clipWidth, width } = props;

        registerZoomHandler((dx: number) => {
            d3.select(this.xAxis).attr('transform', `translate(${clipWidth - width + dx}, ${clipHeight})`);
        });
    }

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
        const { clipWidth, width, clipHeight, margin } = this.props;

        const xAxisProps = {
            className: "x axis",
            transform: `translate(${clipWidth - width}, ${clipHeight})`,
        };

        const xLabelProps = {
            className: "x-label",
            x: clipWidth / 2,
            y: clipHeight + margin.bottom - 16, // 16 is the font size - text is anchored relative to its top
            dy: ".71em",
        };

        return (
            <g>
                <g clipPath="url(#clip-path)">
                    <g ref={(g) => this.xAxis = g}{...xAxisProps} />
                </g>
                <text {...xLabelProps}>Scans</text>
            </g>
        );
    }

    renderYAxis() {
        const { clipHeight, margin } = this.props;

        const yAxisProps = {
            className: "y axis",
        };

        const yLabelProps = {
            className: "y-label",
            x: -clipHeight / 2,
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

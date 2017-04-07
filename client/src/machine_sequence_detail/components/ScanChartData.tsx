import * as React from 'react';

import { IScanChartProps, IScanChartSettings, IZoomable } from './ScanChart';

interface IScanChartDataProps extends IScanChartProps, IScanChartSettings, IZoomable {}

export default class extends React.Component<IScanChartDataProps, {}> {
    g: SVGGElement;

    constructor(props: IScanChartDataProps) {
        super();
        const { registerZoomHandler, clipWidth, width } = props;

        registerZoomHandler((dx: number) => {
            d3.select(this.g).attr('transform', `translate(${clipWidth - width + dx}, 0)`);
        });
    }

    componentDidMount() {
        this.renderPlot();
    }

    componentDidUpdate() {
        this.renderPlot();
    }

    renderPlot() {
        const { data, chart, xScale } = this.props;

        // draw the boxplots
        d3.select(this.g).selectAll(".box")
            .data(data)
            .enter().append("g")
            .attr("transform", (d: any) => `translate(${xScale(d[0])}, 0)`)
            .attr("class", (d: any) => d.passed ? "passed" : "failed")
            .call(chart.width(xScale.rangeBand()));
    }

    render() {
        const { clipWidth, width } = this.props;

        return (
            <g
                ref={(g) => this.g = g}
                transform={`translate(${clipWidth - width}, 0)`}
            />
        );
    }
}

import * as React from 'react';

import { ScanChartProps, ScanChartSettings } from './ScanChart';

export default class extends React.Component<ScanChartProps & ScanChartSettings, {}> {
    g: SVGGElement;

    componentDidMount() {
        this.renderPlot();
    }

    componentDidUpdate() {
        this.renderPlot();
    }

    renderPlot() {
        const { data, chart, xScale, margin } = this.props;

        // draw the boxplots
        d3.select(this.g).selectAll(".box")
            .data(data)
            .enter().append("g")
            .attr("transform", (d: any) => `translate(${xScale(d[0])}, ${margin.top})`)
            .attr("class", (d: any) => d.passed ? "passed" : "failed")
            .call(chart.width(xScale.rangeBand()));
    }

    render() {
        return (
            <g ref={(g) => this.g = g} />
        );
    }
}

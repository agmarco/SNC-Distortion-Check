import * as React from 'react';
import 'd3';

import { ScanChartProps, ScanChartSettings } from './ScanChart';

declare const d3: any;

export default class extends React.Component<ScanChartProps & ScanChartSettings, {}> {
    g: SVGGElement;

    renderPlot() {
        const { data, chart, xScale, margin } = this.props;
        let g = d3.select(this.g);

        // draw the boxplots
        g.selectAll(".box")
            .data(data)
            .enter().append("g")
            .attr("transform", (d: any) => "translate(" +  xScale(d[0])  + "," + margin.top + ")")
            .attr("class", (d: any) => d.passed ? "passed" : "failed")
            .call(chart.width(xScale.rangeBand()));
    }

    componentDidMount() {
        this.renderPlot();
    }

    componentDidUpdate() {
        this.renderPlot();
    }

    render() {
        return (
            <g ref={(g) => this.g = g} />
        );
    }
}

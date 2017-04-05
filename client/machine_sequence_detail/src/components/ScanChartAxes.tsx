import * as React from 'react';
import 'd3';

import { ScanChartProps, ScanChartSettings } from './ScanChart';

declare const d3: any;

export default class extends React.Component<ScanChartProps & ScanChartSettings, {}> {
    g: SVGGElement;

    renderPlot() {
        const { xScale, yScale, margin, height, width, min, max } = this.props;
        let g = d3.select(this.g);

        let xAxis = d3.svg.axis()
            .scale(xScale)
            .orient("bottom")
            .innerTickSize(0)
            .outerTickSize(0)
            .tickPadding(10);

        let yAxis = d3.svg.axis()
            .scale(yScale)
            .orient("left")
            .tickValues(d3.range(min, max, 0.5))
            .innerTickSize(-width)
            .outerTickSize(0)
            .tickPadding(10);

        g.append("g")
            .attr("class", "x axis")
            .attr("transform", "translate(0," + (height + margin.top) + ")")
            .call(xAxis)
            .append("text")
            .attr("x", (width / 2) )
            .attr("y", margin.bottom - 16)
            .attr("dy", ".71em")
            .style("text-anchor", "middle")
            .style("alignment-baseline", "baseline")
            .style("font-size", "16px")
            .text("Scans");

        g.append("g")
            .attr("class", "y axis")
            .call(yAxis)
            .append("text")
            .attr("transform", "rotate(-90)")
            .attr("x", -(height / 2) )
            .attr("y", -margin.left)
            .attr("dy", ".71em")
            .style("text-anchor", "middle")
            .style("font-size", "16px")
            .text("Distortion (mm)");
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

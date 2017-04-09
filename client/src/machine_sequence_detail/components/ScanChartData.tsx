import * as React from 'react';

import { IScanChartProps, IScanChartSettings, IScrollable } from './ScanChart';
import Scrollable from './Scrollable';

interface IScanChartDataProps extends IScanChartProps, IScanChartSettings, IScrollable {}

export default class extends React.Component<IScanChartDataProps, {}> {
    g: SVGGElement;

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
        const { scroll } = this.props;

        return (

            <Scrollable {...scroll}>
                <g ref={(g) => this.g = g} />
            </Scrollable>
        );
    }
}

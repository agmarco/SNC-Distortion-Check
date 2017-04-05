import * as React from 'react';
import 'd3';

import { ScanChartProps, ScanChartSettings } from './ScanChart';

declare const d3: any;

export default class extends React.Component<ScanChartProps & ScanChartSettings, {}> {
    g: SVGGElement;

    renderPlot() {
        const { margin, height, width, max, machineSequencePair } = this.props;
        let g = d3.select(this.g);

        g.append("line")
            .style("stroke", "#900")
            .style("stroke-dasharray", "5, 5")
            .attr("x1", 0)
            .attr("y1", height - (machineSequencePair.tolerance / max * height) + margin.top)
            .attr("x2", width)
            .attr("y2", height - (machineSequencePair.tolerance / max * height) + margin.top);
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

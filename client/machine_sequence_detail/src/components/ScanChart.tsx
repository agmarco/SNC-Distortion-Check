import * as React from 'react';
import 'd3';
import './box';
import './box.scss';

import { MachineSequencePairDTO, ScanDTO } from 'common/service';

declare const d3: any;

interface ScanChartProps {
    machineSequencePair: MachineSequencePairDTO;
    scans: ScanDTO[];
}

export default class extends React.Component<ScanChartProps, {}> {
    svg: any;

    renderPlot() {
        const { machineSequencePair, scans } = this.props;

        // Returns a function to compute the interquartile range.
        function iqr(k: any) {
            return function (d: any, i: number) {
                var q1 = d.quartiles[0],
                    q3 = d.quartiles[2],
                    iqr = (q3 - q1) * k,
                    i = -1,
                    j = d.length;
                while (d[++i] < q1 - iqr);
                while (d[--j] > q3 + iqr);
                return [i, j];
            };
        }

        var labels = true; // show the text labels beside individual boxplots?

        var margin = {top: 20, right: 20, bottom: 60, left: 60};
        var  width = 800 - margin.left - margin.right;
        var height = 400 - margin.top - margin.bottom;

        var allDataPoints = Array.prototype.concat.apply([], scans.map((scan) => scan.distortion));
        var min = 0,
            max = 1.05*Math.max(machineSequencePair.tolerance, Math.max.apply(null, allDataPoints));

        var data = scans.map((scan, i) => [scan.acquisition_date + ' ' + i, scan.distortion]);

        var chart = d3.box()
            .whiskers(iqr(Infinity)) // 1.5
            .height(height)
            .domain([min, max])
            .showLabels(labels);

        var svg = d3.select(this.svg);

        var g = svg.attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .attr("class", "box")
            .append("g")
            .attr("transform", "translate(" + margin.left + ", 0)");

        // the x-axis
        var x = d3.scale.ordinal()
            .domain( data.map(function(d) { return d[0] } ) )
            .rangeRoundBands([0 , width], 0.7, 0.3);

        var xAxis = d3.svg.axis()
            .scale(x)
            .orient("bottom")
            .innerTickSize(0)
            .outerTickSize(0)
            .tickPadding(10);

        // the y-axis
        var y = d3.scale.linear()
            .domain([min, max])
            .range([height + margin.top, margin.top]);

        var yAxis = d3.svg.axis()
            .scale(y)
            .orient("left")
            .tickValues(d3.range(min, max, 0.5))
            .innerTickSize(-width)
            .outerTickSize(0)
            .tickPadding(10);

        // draw the boxplots
        g.selectAll(".box")
            .data(data)
            .enter().append("g")
            .attr("transform", function(d: any) { return "translate(" +  x(d[0])  + "," + margin.top + ")"; } )
            .call(chart.width(x.rangeBand()));

        // draw tolerance line
        g.append("line")
            .style("stroke", "red")
            .style("stroke-dasharray", "5, 5")
            .attr("x1", 0)
            .attr("y1", height - (machineSequencePair.tolerance / max * height) + margin.top) // TODO
            .attr("x2", width)
            .attr("y2", height - (machineSequencePair.tolerance / max * height) + margin.top);

        // draw x axis
        g.append("g")
            .attr("class", "x axis")
            .attr("transform", "translate(0," + (height + margin.top) + ")")
            .call(xAxis)
            .append("text")
            .attr("x", (width / 2) )
            .attr("y", margin.bottom - 16) // TODO
            .attr("dy", ".71em")
            .style("text-anchor", "middle")
            .style("alignment-baseline", "baseline")
            .style("font-size", "16px")
            .text("Scans");

        // draw y axis
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

    render() {
        return (
            <div>
                <h2>Performance over Time</h2>
                <svg ref={(svg) => this.svg = svg} />
            </div>
        );
    }
}

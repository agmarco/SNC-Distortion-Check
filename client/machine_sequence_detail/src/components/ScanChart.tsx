import * as React from 'react';
import 'd3';
import './box';
import './box.scss';

import { ScanDTO } from 'common/service';

declare const d3: any;

interface ScanChartProps {
    scans: ScanDTO[];
}

export default class extends React.Component<ScanChartProps, {}> {
    svg: any;

    renderPlot() {
        const { scans } = this.props;

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

        var margin = {top: 30, right: 50, bottom: 70, left: 50};
        var  width = 800 - margin.left - margin.right;
        var height = 400 - margin.top - margin.bottom;

        var allDataPoints = Array.prototype.concat.apply([], scans.map((scan) => scan.distortion));

        var min = Math.min.apply(null, allDataPoints),
            max = Math.max.apply(null, allDataPoints);

        var data = scans.map((scan, i) => [scan.acquisition_date + ' ' + i, scan.distortion]);

        var chart = d3.box()
            .whiskers(iqr(1.5))
            .height(height)
            .domain([min, max])
            .showLabels(labels);

        var svg = d3.select(this.svg);

        svg.attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .attr("class", "box")
            .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        // the x-axis
        var x = d3.scale.ordinal()
            .domain( data.map(function(d) { return d[0] } ) )
            .rangeRoundBands([0 , width], 0.7, 0.3);

        var xAxis = d3.svg.axis()
            .scale(x)
            .orient("bottom");

        // the y-axis
        var y = d3.scale.linear()
            .domain([min, max])
            .range([height + margin.top, 0 + margin.top]);

        var yAxis = d3.svg.axis()
            .scale(y)
            .orient("left");

        // draw the boxplots
        svg.selectAll(".box")
            .data(data)
            .enter().append("g")
            .attr("transform", function(d: any) { return "translate(" +  x(d[0])  + "," + margin.top + ")"; } )
            .call(chart.width(x.rangeBand()));

        // draw y axis
        svg.append("g")
            .attr("class", "y axis")
            .call(yAxis)
            .append("text") // and text1
            .attr("transform", "rotate(-90)")
            .attr("y", 6)
            .attr("dy", ".71em")
            .style("text-anchor", "end")
            .style("font-size", "16px")
            .text("Distortion (mm)");

        // draw x axis
        svg.append("g")
            .attr("class", "x axis")
            .attr("transform", "translate(0," + (height  + margin.top + 10) + ")")
            .call(xAxis)
            .append("text")             // text label for the x axis
            .attr("x", (width / 2) )
            .attr("y",  10 )
            .attr("dy", ".71em")
            .style("text-anchor", "middle")
            .style("font-size", "16px")
            .text("Scans");
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

import * as React from 'react';

import { MachineSequencePairDTO, ScanDTO } from 'common/service';
import ScanChartData from './ScanChartData';
import ScanChartTolerance from './ScanChartTolerance';
import ScanChartAxes from './ScanChartAxes';

import './ScanChart.scss';

interface ChartData {
    [index: number]: number;
    length: number;
    quartiles: number[];
    passed: boolean;
}

export interface ScanChartSettings {
    labels: boolean;
    margin: {top: number; right: number; bottom: number; left: number};
    width: number;
    height: number;
    min: number;
    max: number;
    data: ChartData[];
    chart: any;
    xScale: any;
    yScale: any;
}

export interface ScanChartProps {
    machineSequencePair: MachineSequencePairDTO;
    scans: ScanDTO[];
}

export default class extends React.Component<ScanChartProps, {}> {

    // Returns a function to compute the interquartile range.
    // Higher values of k will produce fewer outliers.
    iqr(k: number) {
        return (d: ChartData, i: number) => {
            let q1 = d.quartiles[0];
            let q3 = d.quartiles[2];
            let iqr = (q3 - q1) * k;
            i = -1;
            let j = d.length;
            while (d[++i] < q1 - iqr) { }
            while (d[--j] > q3 + iqr) { }
            return [i, j];
        };
    }

    settings() {
        const { machineSequencePair, scans } = this.props;
        const allDataPoints = Array.prototype.concat.apply([], scans.map((scan) => scan.distortion));

        const labels = true;
        const margin = {top: 0, right: 0, bottom: 60, left: 60};

        const width = 800 - margin.left - margin.right;
        const height = 400 - margin.top - margin.bottom;

        const min = 0;
        const max = 1.05*Math.max.apply(null, [machineSequencePair.tolerance, ...allDataPoints]);

        const data = scans.map((scan) => {
            const array = [scan.acquisition_date, scan.distortion] as any;
            array.passed = scan.passed;
            return array;
        });

        const chart = d3.box()
            .whiskers(this.iqr(Infinity)) // 1.5
            .height(height)
            .domain([min, max])
            .showLabels(labels);

        const xScale = d3.scale.ordinal()
            .domain(data.map(function(d) { return d[0] }))
            .rangeRoundBands([0 , width], 0.7, 0.3);

        const yScale = d3.scale.linear()
            .domain([min, max])
            .range([height + margin.top, margin.top]);

        return {
            labels,
            margin,
            width,
            height,
            min,
            max,
            data,
            chart,
            xScale,
            yScale,
        }
    }

    render() {
        const settings = this.settings();
        const { width, height, margin } = settings;

        return (
            <svg
                width={width + margin.left + margin.right}
                height={height + margin.top + margin.bottom}
                className="box"
            >
                <g transform={`translate(${margin.left}, 0)`}>
                    <ScanChartData {...this.props} {...settings} />
                    <ScanChartTolerance {...this.props} {...settings} />
                    <ScanChartAxes {...this.props} {...settings} />
                </g>
            </svg>
        );
    }
}

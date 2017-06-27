import React from 'react';
import format from 'date-fns/format';
import 'd3';

import { IMachineSequencePairDto, IScanDto } from 'common/service';
import ScanChartData from './ScanChartData';
import ScanChartTolerance from './ScanChartTolerance';
import ScanChartAxes from './ScanChartAxes';
import '../box.js';

import './ScanChart.scss';

export interface IScrollable {
    scroll: {
        start: number;
        dx: number;
        clipPathId: string;
    };
}

interface IScanDistortion extends Array<number> {
    quartiles: number[];
}

type ScanTuple = [number, IScanDistortion]; // [pk, error_mags]

export interface IScanData extends ScanTuple {
    passed: boolean;
    label: string;
}

export interface IScanChartSettings {
    labels: boolean;
    margin: {top: number; right: number; bottom: number; left: number};
    clipWidth: number;
    width: number;
    height: number;
    yMin: number;
    yMax: number;
    data: IScanData[];
    chart: any;
    xScale: any;
    yScale: any;
}

export interface IScanChartProps {
    machineSequencePair: IMachineSequencePairDto;
    scans: IScanDto[];
    tolerance: number;
}

export interface IScanChartState {
    scrollX: number;
}

const chartHelp = 'This box-and-whiskers chart should let you, at a glance, determine ' +
    'whether this machine-sequence combination\'s geometric distortion is within the ' +
    'allowed tolerance.  The top whisker, top edge of the box, middle of the box, bottom edge ' +
    'of the box, and bottom whisker correspond to the 100-, 75-, 50-, 25-, and 0-th percentiles ' +
    'of the magnitude of the distortion found in the scan.  Red data points indicate that ' +
    'the maximum distortion was above the tolerance set when the analysis was performed.';

export default class extends React.Component<IScanChartProps, IScanChartState> {
    svg: SVGElement;
    settings: IScanChartSettings;

    constructor(props: IScanChartProps) {
        super();
        this.settings = this.getSettings(props);
        this.state = {scrollX: 0};
    }

    // Returns a function to compute the interquartile range.
    // Higher values of k will produce fewer outliers.
    iqr(k: number) {
        return (d: IScanDistortion, i: number) => {
            let q1 = d.quartiles[0];
            let q3 = d.quartiles[2];
            let iqr = (q3 - q1) * k;
            i = 0;
            let j = d.length - 1;
            while (d[i] < q1 - iqr) {
                i++;
            }
            while (d[j] > q3 + iqr) {
                j--;
            }
            return [i, j];
        };
    }

    getSettings(props: IScanChartProps) {
        const { machineSequencePair, scans } = props;
        const processedScans = scans.filter(s => !s.processing && !s.errors).reverse();

        const labels = true;
        const margin = {top: 10, right: 10, bottom: 60, left: 60};

        // TODO make the width responsive
        const clipWidth = 800 - margin.left - margin.right;
        const width = Math.max(processedScans.length * 100, clipWidth);
        const height = 400 - margin.top - margin.bottom;

        const maxDistortion = Math.max(...processedScans.map(s => Math.max(...s.error_mags as number[])));
        const yMin = 0;
        const yMax = 1.05 * Math.max(machineSequencePair.tolerance, maxDistortion);

        const data = processedScans.map((scan) => {
            const array = [scan.pk, scan.error_mags] as any;
            array.passed = scan.passed;
            array.label = format(scan.acquisition_date, 'D MMM YYYY');
            return array;
        });

        const chart = d3.box()
            .whiskers(this.iqr(Infinity)) // 1.5
            .height(height)
            .domain([yMin, yMax])
            .showLabels(labels);

        const xScale = d3.scale.ordinal()
            .domain(data.map(d => d[0]))
            .rangeRoundBands([0, width], 0.7, 0.3);

        const yScale = d3.scale.linear()
            .domain([yMin, yMax])
            .range([height, 0]);

        return {
            labels,
            margin,
            clipWidth,
            width,
            height,
            yMin,
            yMax,
            data,
            chart,
            xScale,
            yScale,
        };
    }

    componentDidMount() {
        const { clipWidth, width } = this.settings;

        const scroll = d3.behavior.zoom()
            .on('zoom', () => {
                const { scrollX } = this.state;
                let newScrollX = scrollX;

                if (d3.event.sourceEvent.type === 'wheel') {

                    // d3.event.translate is wrong because it's expecting this event to zoom.
                    // Instead, keep a reference to the current x translation, and add the
                    // extent of the vertical wheel scroll.
                    newScrollX += d3.event.sourceEvent.deltaY;
                } else if (d3.event.sourceEvent.type === 'mousemove') {
                    newScrollX = d3.event.translate[0];
                }

                // Don't let the user scroll beyond the bounds of the chart.
                newScrollX = Math.min(Math.max(newScrollX, 0), width - clipWidth);
                scroll.translate([newScrollX, 0]);
                this.setState({scrollX: newScrollX});
            });

        d3.select(this.svg).call(scroll);
    }

    render() {
        const { clipWidth, width, height, margin } = this.settings;
        const { scrollX } = this.state;
        const clipPathId = 'clip-path';
        const scroll = {
            start: clipWidth - width,
            dx: scrollX,
            clipPathId,
        };

        return (
            <svg
                width={clipWidth + margin.left + margin.right}
                height={height + margin.top + margin.bottom}
                className="scan-chart box"
                ref={svg => this.svg = svg}
            >
                <title>{chartHelp}</title>
                <defs>
                    <clipPath id={clipPathId}>
                        <rect width={clipWidth} height={height + margin.top + margin.bottom} />
                    </clipPath>
                </defs>
                <g transform={`translate(${margin.left}, ${margin.top})`}>
                    <ScanChartAxes {...this.props} {...this.settings} scroll={scroll} />
                    <ScanChartTolerance {...this.props} {...this.settings} scroll={scroll} />
                    <ScanChartData {...this.props} {...this.settings} scroll={scroll} />
                    <rect width={clipWidth} height={height} className="border" />
                </g>
            </svg>
        );
    }
}

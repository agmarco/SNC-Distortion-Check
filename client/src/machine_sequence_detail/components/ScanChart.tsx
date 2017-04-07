import * as React from 'react';

import { IMachineSequencePairDTO, IScanDTO } from 'common/service';
import ScanChartData from './ScanChartData';
import ScanChartTolerance from './ScanChartTolerance';
import ScanChartAxes from './ScanChartAxes';

import './ScanChart.scss';

interface IScanData {
    [index: number]: number;
    length: number;
    quartiles: number[];
    passed: boolean;
}

interface IZoomHandler {
    (dx: number): void;
}

export interface IZoomable {
    registerZoomHandler: (handler: IZoomHandler) => void;
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
    machineSequencePair: IMachineSequencePairDTO;
    scans: IScanDTO[];
}

export default class extends React.Component<IScanChartProps, {}> {
    svg: SVGElement;
    settings: IScanChartSettings;
    zoomHandlers: IZoomHandler[] = [];

    constructor(props: IScanChartProps) {
        super();
        this.settings = this.getSettings(props);
    }

    // Returns a function to compute the interquartile range.
    // Higher values of k will produce fewer outliers.
    iqr(k: number) {
        return (d: IScanData, i: number) => {
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
        const allDataPoints = Array.prototype.concat.apply([], scans.map((scan) => scan.distortion));

        const labels = true;
        const margin = {top: 10, right: 10, bottom: 60, left: 60};

        const clipWidth = 800 - margin.left - margin.right;
        const height = 400 - margin.top - margin.bottom;

        const yMin = 0;
        const yMax = 1.05 * Math.max.apply(null, [machineSequencePair.tolerance, ...allDataPoints]);

        const width = Math.max(scans.length * 80, clipWidth);

        const data = scans.map((scan) => {
            const array = [scan.acquisition_date, scan.distortion] as any;
            array.passed = scan.passed;
            return array;
        });

        const chart = d3.box()
            .whiskers(this.iqr(Infinity)) // 1.5
            .height(height)
            .domain([yMin, yMax])
            .showLabels(labels);

        const xScale = d3.scale.ordinal()
            .domain(data.map((d) => d[0]))
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

    renderPlot() {
        const { clipWidth, width } = this.settings;

        const zoom = d3.behavior.zoom()
            .on('zoom', () => {

                // TODO mouse scroll doesn't work properly
                let [dx] = zoom.translate();
                dx = Math.min(Math.max(dx, 0), width - clipWidth);
                zoom.translate([dx, 0]);

                for (let handler of this.zoomHandlers) {
                    handler(dx);
                }
            });

        d3.select(this.svg).call(zoom);
    }

    registerZoomHandler(handler: IZoomHandler) {
        this.zoomHandlers.push(handler);
    }

    componentDidMount() {
        this.renderPlot();
    }

    componentDidUpdate() {
        this.renderPlot();
    }

    render() {
        const { clipWidth, height, margin } = this.settings;

        return (
            <svg
                width={clipWidth + margin.left + margin.right}
                height={height + margin.top + margin.bottom}
                className="box"
                ref={(svg) => this.svg = svg}
            >
                <defs>
                    <clipPath id="clip-path">
                        <rect width={clipWidth} height={height + margin.top + margin.bottom} />
                    </clipPath>
                </defs>
                <g transform={`translate(${margin.left}, ${margin.top})`}>
                    <g clipPath="url(#clip-path)">
                        <ScanChartData
                            {...this.props}
                            {...this.settings}
                            registerZoomHandler={this.registerZoomHandler.bind(this)}
                        />
                        <ScanChartTolerance
                            {...this.props}
                            {...this.settings}
                            registerZoomHandler={this.registerZoomHandler.bind(this)}
                        />
                    </g>
                    <ScanChartAxes
                        {...this.props}
                        {...this.settings}
                        registerZoomHandler={this.registerZoomHandler.bind(this)}
                    />
                </g>
            </svg>
        );
    }
}

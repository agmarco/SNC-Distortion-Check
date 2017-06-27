import React from 'react';
import $ from 'jquery';
import { assert } from 'chai';
import { shallow, mount, ShallowWrapper, ReactWrapper } from 'enzyme';

import * as fixtures from 'common/fixtures';
import { default as ScanTable, IScanTableProps, IScanTableState } from './components/ScanTable';
import { default as ScanChart, IScanChartProps, IScanChartState } from './components/ScanChart';
import ScanChartData from './components/ScanChartData';
import { IScanDto, IPhantomDto } from 'common/service';

describe('<ScanTable />', () => {
    let phantomA: IPhantomDto;
    let phantomB: IPhantomDto;
    let wrapper: ShallowWrapper<IScanTableProps, IScanTableState>;

    beforeEach(() => {
        phantomA = fixtures.phantomFixture();
        phantomB = fixtures.phantomFixture();

        const scans = [
            fixtures.scanFixture(phantomA),
            fixtures.scanFixture(phantomB),
        ];

        wrapper = shallow<IScanTableProps, IScanTableState>(
            <ScanTable scans={scans} uploadScanUrl="" pollScansError={null} />
        );
    });

    it('filters by phantom', () => {
        wrapper.find('.phantom-filter').first().simulate('change', {target: {value: phantomA.pk.toString()}});
        const results = wrapper.find('.results').find('tbody').find('tr');
        const phantomDisplay = `${phantomA.model_number} — ${phantomA.serial_number}`;
        assert(results.everyWhere(r => r.find('td').at(2).text() === phantomDisplay));
    });
});

describe('<ScanChart />', () => {
    let app: JQuery;
    let scanA: IScanDto;
    let scanB: IScanDto;
    let wrapper: ReactWrapper<IScanChartProps, IScanChartState>;

    beforeEach(() => {
        app = $('#app');

        scanA = fixtures.scanFixture();
        scanB = fixtures.scanFixture();

        scanA.error_mags = [
            2.1850395487480587,
            0.8065866998556279,
            1.425678550748541,
            1.6661102033492017,
            1.7346037030049957,
            1.3128036339751563,
            1.930314810061184,
            1.215615536609391,
            2.031341708678863,
            0.9354963306802303,
        ];

        scanA.passed = true;
        scanB.passed = false;

        const machineSequencePair = fixtures.machineSequencePairFixture();
        const scans = [scanA, scanB];

        // this takes awhile -- had to increase timeout
        wrapper = mount<IScanChartProps, IScanChartState>(
            <ScanChart machineSequencePair={machineSequencePair} scans={scans} tolerance={1} />,
            {attachTo: app[0]},
        );
    });

    it('calculates the quartiles correctly', () => {
        const quartiles = wrapper.find(ScanChartData).prop('data')[1][1].quartiles;

        assert(quartiles[0] === 1.215615536609391);
        assert(quartiles[1] === 1.5458943770488713);
        assert(quartiles[2] === 1.930314810061184);
    });

    it('marks scans as passed/failed', () => {
        const scanAPlot = app.find('.box-and-whiskers').eq(0);
        const scanBPlot = app.find('.box-and-whiskers').eq(1);

        assert(scanAPlot.hasClass('failed'));
        assert(scanBPlot.hasClass('passed'));
    });
});

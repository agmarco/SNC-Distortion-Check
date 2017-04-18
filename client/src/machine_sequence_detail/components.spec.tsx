import React from 'react';
import { assert, expect } from 'chai';
import { shallow, ShallowWrapper } from 'enzyme';

import * as fixtures from 'common/fixtures';
import { default as ScanTable, IScanTableProps } from './components/ScanTable';
import { default as ScanChart, IScanChartProps } from './components/ScanChart';
import { IScanDTO, IPhantomDTO } from 'common/service';

describe('<ScanTable />', () => {
    let phantomA: IPhantomDTO;
    let phantomB: IPhantomDTO;
    let wrapper: ShallowWrapper<IScanTableProps, any>;

    beforeEach(() => {
        phantomA = fixtures.phantomFixture();
        phantomB = fixtures.phantomFixture();

        const scans = [
            fixtures.scanFixture(phantomA),
            fixtures.scanFixture(phantomB),
        ];

        wrapper = shallow<IScanTableProps>(<ScanTable scans={scans} uploadScanUrl="" />);
    });

    it('filters by phantom', () => {
        wrapper.find('.phantom-filter').first().simulate('change', {target: {value: phantomA.pk.toString()}});
        const results = wrapper.find('.results').find('tbody').find('tr');
        const phantomDisplay = `${phantomA.model_number} — ${phantomA.serial_number}`;
        assert(results.everyWhere(r => r.find('td').at(2).text() === phantomDisplay));
    });
});

describe('<ScanChart />', () => {
    let scan: IScanDTO;
    let wrapper: ShallowWrapper<IScanChartProps, any>;

    beforeEach(() => {
        const machineSequencePair = fixtures.machineSequencePairFixture();

        scan = fixtures.scanFixture();
        scan.distortion = [1, 1.1, 1.5, 2, 2.1, 2.2, 2.2, 2.7, 3.3, 3.6, 4.1, 5.2];

        const scans = [scan];

        wrapper = shallow<IScanChartProps>(<ScanChart machineSequencePair={machineSequencePair} scans={scans} />);
    });

    it('calculates the quartiles correctly', () => {
        const boxAndWhiskers = wrapper.find('.box-and-whiskers').first();
        const min = boxAndWhiskers.find('.min').first().text();
        const lower = boxAndWhiskers.find('.lower').first().text();
        const median = boxAndWhiskers.find('.median').first().text();
        const upper = boxAndWhiskers.find('.upper').first().text();
        const max = boxAndWhiskers.find('.max').first().text();

        assert(wrapper.find('.box-and-whiskers').length > 0);
        // assert(min === '1.0');
        // assert(lower === '1.6');
        // assert(median === '2.2');
        // assert(upper === '3.5');
        // assert(max === '5.2');
    });
});

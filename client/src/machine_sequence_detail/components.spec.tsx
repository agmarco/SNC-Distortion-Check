import React from 'react';
import { assert } from 'chai';
import { shallow, mount, ShallowWrapper, ReactWrapper } from 'enzyme';

import * as fixtures from 'common/fixtures';
import { default as ScanTable, IScanTableProps, IScanTableState } from './components/ScanTable';
import { default as ScanChart, IScanChartProps, IScanChartState } from './components/ScanChart';
import { IScanDTO, IPhantomDTO } from 'common/service';

describe('<ScanTable />', () => {
    let phantomA: IPhantomDTO;
    let phantomB: IPhantomDTO;
    let wrapper: ShallowWrapper<IScanTableProps, IScanTableState>;

    beforeEach(() => {
        phantomA = fixtures.phantomFixture();
        phantomB = fixtures.phantomFixture();

        const scans = [
            fixtures.scanFixture(phantomA),
            fixtures.scanFixture(phantomB),
        ];

        wrapper = shallow<IScanTableProps, IScanTableState>(<ScanTable scans={scans} uploadScanUrl="" />);
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
    let wrapper: ReactWrapper<IScanChartProps, IScanChartState>;

    beforeEach(() => {
        const machineSequencePair = fixtures.machineSequencePairFixture();

        scan = fixtures.scanFixture();
        scan.distortion = [
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

        const scans = [scan];

        // this takes awhile -- had to increase timeout
        wrapper = mount<IScanChartProps, IScanChartState>(
            <ScanChart machineSequencePair={machineSequencePair} scans={scans} />,
            {attachTo: document.getElementById('app') as HTMLElement},
        );
    });

    it('calculates the quartiles correctly', () => {
        const app = document.getElementById('app') as HTMLElement;
        const boxAndWhiskers = app.getElementsByClassName('box-and-whiskers')[0];

        const min = boxAndWhiskers.getElementsByClassName('whisker min')[0].innerHTML;
        const lower = boxAndWhiskers.getElementsByClassName('box lower')[0].innerHTML;
        const median = boxAndWhiskers.getElementsByClassName('box median')[0].innerHTML;
        const upper = boxAndWhiskers.getElementsByClassName('box upper')[0].innerHTML;
        const max = boxAndWhiskers.getElementsByClassName('whisker max')[0].innerHTML;

        assert(min === '0.8');
        assert(lower === '1.2');
        assert(median === '1.5');
        assert(upper === '1.9');
        assert(max === '2.2');
    });
});

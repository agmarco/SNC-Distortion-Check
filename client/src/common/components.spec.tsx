import React from 'react';
import { assert } from 'chai';
import { shallow, ShallowWrapper } from 'enzyme';

import { default as MachineSequenceTable, IMachineSequenceTableProps } from './components/MachineSequenceTable';
import { machineFixture, sequenceFixture, machineSequencePairFixture } from './fixtures';
import { IMachineDTO, ISequenceDTO } from './service';

describe('<MachineSequenceTable />', () => {
    let machineA: IMachineDTO;
    let machineB: IMachineDTO;
    let sequenceA: ISequenceDTO;
    let sequenceB: ISequenceDTO;
    let wrapper: ShallowWrapper<IMachineSequenceTableProps, any>;

    beforeEach(() => {
        machineA = machineFixture();
        machineB = machineFixture();

        sequenceA = sequenceFixture();
        sequenceB = sequenceFixture();

        const machineSequencePairs = [
            machineSequencePairFixture(machineA, sequenceA),
            machineSequencePairFixture(machineA, sequenceB),
            machineSequencePairFixture(machineB, sequenceA),
            machineSequencePairFixture(machineB, sequenceB),
        ];

        wrapper = shallow<IMachineSequenceTableProps>(
            <MachineSequenceTable machineSequencePairs={machineSequencePairs} uploadScanUrl="" />
        );
    });

    it('filters by machine', () => {
        wrapper.find('.machine-filter').first().simulate('change', {target: {value: machineA.pk.toString()}});
        const results = wrapper.find('.results').find('tbody').find('tr');
        assert(results.everyWhere(r => r.find('td').at(0).text() === machineA.name));
    });

    it('filters by sequence', () => {
        wrapper.find('.sequence-filter').first().simulate('change', {target: {value: sequenceA.pk.toString()}});
        const results = wrapper.find('.results').find('tbody').find('tr');
        assert(results.everyWhere(r => r.find('td').at(1).text() === sequenceA.name));
    });
});

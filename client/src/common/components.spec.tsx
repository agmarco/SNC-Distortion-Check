import React from 'react';
import { assert } from 'chai';
import { shallow, ShallowWrapper } from 'enzyme';

import {
    default as MachineSequenceTable,
    IMachineSequenceTableProps,
    IMachineSequenceTableState,
} from './components/MachineSequenceTable';
import { machineFixture, sequenceFixture, machineSequencePairFixture } from './fixtures';
import { IMachineDTO, ISequenceDTO } from './service';

describe('<MachineSequenceTable />', () => {
    let machineA: IMachineDTO;
    let machineB: IMachineDTO;
    let sequenceA: ISequenceDTO;
    let sequenceB: ISequenceDTO;
    let wrapper: ShallowWrapper<IMachineSequenceTableProps, IMachineSequenceTableState>;

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

        wrapper = shallow<IMachineSequenceTableProps, IMachineSequenceTableState>(
            <MachineSequenceTable machineSequencePairs={machineSequencePairs} uploadScanUrl="" />
        );
    });

    it('filters by machine', () => {
        wrapper.find('.machine-filter').first().simulate('change', {target: {value: machineA.pk.toString()}});
        const results = wrapper.find('.results').find('tbody').find('tr');
        const machineColumnIndex = 0;
        assert(results.everyWhere(r => r.find('td').at(machineColumnIndex).text() === machineA.name));
    });

    it('filters by sequence', () => {
        wrapper.find('.sequence-filter').first().simulate('change', {target: {value: sequenceA.pk.toString()}});
        const results = wrapper.find('.results').find('tbody').find('tr');
        const sequenceColumnIndex = 1;
        assert(results.everyWhere(r => r.find('td').at(sequenceColumnIndex).text() === sequenceA.name));
    });
});

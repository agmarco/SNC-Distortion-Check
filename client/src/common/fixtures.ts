import uniqueId from 'lodash/uniqueId';

import { IMachineDTO, ISequenceDTO } from './service';

export const machineFixture = () => {
    const pk = Number(uniqueId());
    return {
        pk,
        name: `Machine ${pk}`,
        model: `Model ${pk}`,
        manufacturer: `Manufacturer ${pk}`,
    };
};

export const sequenceFixture = () => {
    const pk = Number(uniqueId());
    return {
        pk,
        name: `Sequence ${pk}`,
        instructions: `Instructions ${pk}`,
    };
};

export const machineSequencePairFixture = (machine: IMachineDTO, sequence: ISequenceDTO) => {
    const pk = Number(uniqueId());
    return {
        pk,
        machine,
        sequence,
        latest_scan_date: null,
        latest_scan_passed: null,
        detail_url: '',
        tolerance: 1,
    };
};

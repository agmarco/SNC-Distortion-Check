import uniqueId from 'lodash/uniqueId';

import { IMachineDto, ISequenceDto, IMachineSequencePairDto, IPhantomDto, IScanDto } from './service';

export const machineFixture = (): IMachineDto => {
    const pk = Number(uniqueId());
    return {
        pk,
        name: `Machine ${pk}`,
        model: `Model ${pk}`,
        manufacturer: `Manufacturer ${pk}`,
    };
};

export const sequenceFixture = (): ISequenceDto => {
    const pk = Number(uniqueId());
    return {
        pk,
        name: `Sequence ${pk}`,
        instructions: `Instructions ${pk}`,
    };
};

export const machineSequencePairFixture = (machine?: IMachineDto, sequence?: ISequenceDto): IMachineSequencePairDto => {
    const pk = Number(uniqueId());
    return {
        pk,
        machine: machine || machineFixture(),
        sequence: sequence || sequenceFixture(),
        latest_scan_date: null,
        latest_scan_passed: null,
        detail_url: '',
        tolerance: 3,
    };
};

export const phantomFixture = (): IPhantomDto => {
    const pk = Number(uniqueId());
    return {
        pk,
        name: `Name ${pk}`,
        model_number: `Model ${pk}`,
        serial_number: `Serial ${pk}`,
        gold_standard_grid_locations: `Gold Standard ${pk}`,
    };
};

export const scanFixture = (phantom?: IPhantomDto): IScanDto => {
    const pk = Number(uniqueId());
    return {
        pk,
        phantom: phantom || phantomFixture(),
        processing: false,
        errors: null,
        passed: true,
        acquisition_date: '2000-01-01',
        errors_url: `/scans/${pk}/errors/`,
        delete_url: `/scans/${pk}/delete/`,
        dicom_overlay_url: `/scans/${pk}/dicom-overlay/`,
        raw_data_url: `/scans/${pk}/raw-data/`,
        refresh_url: `/scans/${pk}/refresh/`,
        full_report_url: null,
        executive_report_url: null,
        error_mags: [],
    };
};

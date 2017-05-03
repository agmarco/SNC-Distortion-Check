import uniqueId from 'lodash/uniqueId';

import { IMachineDTO, ISequenceDTO, IMachineSequencePairDTO, IPhantomDTO, IScanDTO } from './service';

export const machineFixture = (): IMachineDTO => {
    const pk = Number(uniqueId());
    return {
        pk,
        name: `Machine ${pk}`,
        model: `Model ${pk}`,
        manufacturer: `Manufacturer ${pk}`,
    };
};

export const sequenceFixture = (): ISequenceDTO => {
    const pk = Number(uniqueId());
    return {
        pk,
        name: `Sequence ${pk}`,
        instructions: `Instructions ${pk}`,
    };
};

export const machineSequencePairFixture = (machine?: IMachineDTO, sequence?: ISequenceDTO): IMachineSequencePairDTO => {
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

export const phantomFixture = (): IPhantomDTO => {
    const pk = Number(uniqueId());
    return {
        pk,
        name: `Name ${pk}`,
        model_number: `Model ${pk}`,
        serial_number: `Serial ${pk}`,
        gold_standard_grid_locations: `Gold Standard ${pk}`,
    };
};

export const scanFixture = (phantom?: IPhantomDTO): IScanDTO => {
    const pk = Number(uniqueId());
    return {
        pk,
        phantom: phantom || phantomFixture(),
        processing: false,
        errors: null,
        passed: true,
        acquisition_date: '2000-01-01',
        errors_url: `/${pk}/errors/`,
        delete_url: `/${pk}/delete/`,
        dicom_overlay_url: `/${pk}/dicom-overlay/`,
        zipped_dicom_files_url: `/${pk}/dicom-files/`,
        full_report_url: null,
        executive_report_url: null,
        error_mags: [],
    };
};

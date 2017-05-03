export interface IMachineDTO {
    pk: number;
    name: string;
    model: string;
    manufacturer: string;
}

export interface ISequenceDTO {
    pk: number;
    name: string;
    instructions: string;
}

export interface IMachineSequencePairDTO {
    pk: number;
    machine: IMachineDTO;
    sequence: ISequenceDTO;
    latest_scan_date: string | null;
    latest_scan_passed: boolean | null;
    detail_url: string;
    tolerance: number;
}

export interface IPhantomDTO {
    pk: number;
    name: string;
    model_number: string;
    serial_number: string;
    gold_standard_grid_locations: string;
}

export interface IScanDTO {
    pk: number;
    phantom: IPhantomDTO;
    processing: boolean;
    errors: string | null;
    passed: boolean | null;
    acquisition_date: string;
    errors_url: string;
    delete_url: string;
    dicom_overlay_url: string;
    raw_data_url: string;
    full_report_url: string | null;
    executive_report_url: string | null;
    error_mags: number[] | null;
}

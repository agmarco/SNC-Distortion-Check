export interface IMachineDto {
    pk: number;
    name: string;
    model: string;
    manufacturer: string;
}

export interface ISequenceDto {
    pk: number;
    name: string;
    instructions: string;
}

export interface IMachineSequencePairDto {
    pk: number;
    machine: IMachineDto;
    sequence: ISequenceDto;
    latest_scan_date: string | null;
    latest_scan_passed: boolean | null;
    detail_url: string;
    tolerance: number;
}

export interface IPhantomDto {
    pk: number;
    name: string;
    model_number: string;
    serial_number: string;
    gold_standard_grid_locations: string;
}

export interface IScanDto {
    pk: number;
    phantom: IPhantomDto;
    processing: boolean;
    errors: string | null;
    passed: boolean | null;
    acquisition_date: string;
    errors_url: string;
    delete_url: string;
    dicom_overlay_url: string;
    raw_data_url: string;
    refresh_url: string;
    full_report_url: string | null;
    executive_report_url: string | null;
    error_mags: number[] | null;
}

export interface IGoldenFiducialsDto {
    pk: number;
    is_active: boolean;
    created_on: string;
    type: string;
    processing: boolean;
    dicom_series_filename: string;
    zipped_dicom_files_url: string;
    csv_url: string;
    activate_url: string;
    delete_url: string;
}

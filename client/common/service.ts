export interface MachineDTO {
    pk: number;
    name: string;
    model: string;
    manufacturer: string;
}

export interface SequenceDTO {
    pk: number;
    name: string;
    instructions: string;
}

export interface MachineSequencePairDTO {
    pk: number;
    machine: MachineDTO;
    sequence: SequenceDTO;
    latest_scan_date: string;
    latest_scan_passed: boolean;
    detail_url: string;
}

export interface PhantomDTO {
    pk: number;
    name: string;
    model_number: string;
    serial_number: string;
    gold_standard_grid_locations: string;
}

export interface ScanDTO {
    pk: number;
    phantom: PhantomDTO;
    processing: boolean;
    errors: string;
    passed: boolean;
    acquisition_date: string;
    errors_url: string;
    delete_url: string;
    zipped_dicom_files_url: string;
}

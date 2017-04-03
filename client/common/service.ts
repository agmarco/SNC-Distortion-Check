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
    latest_scan_within_tolerance: boolean;
    detail_url: string;
}

export interface PhantomDTO {
    pk: number;
    name: string;
    model_number: string;
    serial_number: string;
    gold_standard_grid_locations: string;
}

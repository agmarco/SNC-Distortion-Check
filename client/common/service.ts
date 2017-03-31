export interface MachineSequencePairDTO {
    pk: number;
    machine: number;
    sequence: number;
    latest_scan_date: string;
    latest_scan_within_tolerance: boolean;
    detail_url: string;
}

export interface MachineDTO {
    pk: number;
    name: string;
}

export interface SequenceDTO {
    pk: number;
    name: string;
}

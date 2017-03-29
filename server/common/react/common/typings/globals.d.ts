interface MachineSequencePair {
    pk: number;
    machine: number;
    sequence: number;
    latest_scan_date: string;
    latest_scan_within_tolerance: boolean;
    detail_url: string;
}

interface Machine {
    pk: number;
    name: string;
}

interface Sequence {
    pk: number;
    name: string;
}

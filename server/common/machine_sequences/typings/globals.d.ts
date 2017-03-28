interface MachineSequencePair {
    pk: number;
    machine: number;
    sequence: number;
    latest_scan_date: string;
    latest_scan_within_tolerance: boolean;
}

interface Machine {
    pk: number;
    name: string;
}

interface Sequence {
    pk: number;
    name: string;
}

declare const __MACHINE_SEQUENCE_PAIRS__: MachineSequencePair[];
declare const __MACHINES__: Machine[];
declare const __SEQUENCES__: Sequence[];

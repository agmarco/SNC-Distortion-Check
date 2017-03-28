interface SerializedDjangoModel<T> {
    model: string;
    pk: number;
    fields: T;
}

interface CommonFields {
    deleted: boolean;
    created_on: string;
    last_modified_on: string;
}

interface MachineSequencePair extends CommonFields {
    machine: number;
    sequence: number;
    tolerance: number;
}

interface Machine extends CommonFields {
    name: string;
    model: string;
    manufacturer: string;
    institution: number;
}

interface Sequence extends CommonFields {
    name: string;
    institution: number;
    instructions: string;
}

declare const __MACHINE_SEQUENCE_PAIRS__: SerializedDjangoModel<MachineSequencePair>[];
declare const __MACHINES__: SerializedDjangoModel<Machine>[];
declare const __SEQUENCES__: SerializedDjangoModel<Sequence>[];

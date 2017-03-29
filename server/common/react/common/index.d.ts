import * as React from 'react';

export interface MachineSequencePair {
    pk: number;
    machine: number;
    sequence: number;
    latest_scan_date: string;
    latest_scan_within_tolerance: boolean;
    detail_url: string;
}

export interface Machine {
    pk: number;
    name: string;
}

export interface Sequence {
    pk: number;
    name: string;
}

export interface MachineSequenceTableProps {
    machineSequencePairs: MachineSequencePair[];
    machines: Machine[];
    sequences: Sequence[];
}

interface MachineSequenceTableState {
    currentMachine: string|number;
    currentSequence: string|number;
}

export class MachineSequenceTable extends React.Component<MachineSequenceTableProps, MachineSequenceTableState> {
	componentWillMount(): void;
	render(): JSX.Element;
}

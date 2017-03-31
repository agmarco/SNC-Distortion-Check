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
    model_number: string;
    manufacturer: string;
}

export interface Sequence {
    pk: number;
    name: string;
    instructions: string;
}

export interface Phantom {
    pk: number;
    name: string;
    model: number;
    serial_number: string;
    gold_standard_grid_locations: string;
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

export function handleErrors(res: Response, success: () => void): void;

export function encode(data: any): string;

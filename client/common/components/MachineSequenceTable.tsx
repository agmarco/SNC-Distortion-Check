import * as React from 'react';
import { format } from 'date-fns';
import uniqBy from 'lodash/uniqBy';
import { MachineSequencePairDTO, MachineDTO, SequenceDTO } from '../service';
import BoolIcon from './BoolIcon';

interface MachineSequenceTableProps {
    machineSequencePairs: MachineSequencePairDTO[];
}

interface MachineSequenceTableState {
    machines: MachineDTO[];
    sequences: SequenceDTO[];
    currentMachine: string|number;
    currentSequence: string|number;
}

export default class extends React.Component<MachineSequenceTableProps, MachineSequenceTableState> {
    constructor(props: MachineSequenceTableProps) {
        super();

        this.state = {
            machines: uniqBy(props.machineSequencePairs, (pair) => pair.machine.pk).map((pair) => pair.machine),
            sequences: uniqBy(props.machineSequencePairs, (pair) => pair.sequence.pk).map((pair) => pair.sequence),
            currentMachine: 'all',
            currentSequence: 'all',
        }
    }

    filteredMachineSequencePairs() {
        const { machineSequencePairs } = this.props;
        const { currentMachine, currentSequence } = this.state;
        const filters: ((pair: MachineSequencePairDTO) => boolean)[] = [];

        if (currentMachine != 'all') {
            filters.push((pair) => pair.machine.pk == currentMachine);
        }
        if (currentSequence != 'all') {
            filters.push((pair) => pair.sequence.pk == currentSequence);
        }

        return machineSequencePairs.filter((pair) => filters.every((filter) => filter(pair)));
    }

    handleMachineChange(event: React.FormEvent<HTMLInputElement>) {
        this.setState({currentMachine: (event.target as any).value});
    }

    handleSequenceChange(event: React.FormEvent<HTMLInputElement>) {
        this.setState({currentSequence: (event.target as any).value});
    }

    render() {
        const { machines, sequences, currentMachine, currentSequence } = this.state;
        const filteredMachineSequencePairs = this.filteredMachineSequencePairs();

        return (
            <div>
                <a href="#">Upload New Scan</a>
                <div>
                    Filter By
                    <select value={currentMachine} onChange={this.handleMachineChange.bind(this)}>
                        <option value="all">All Machines</option>
                        {machines.map((machine) => <option value={machine.pk} key={machine.pk}>{machine.name}</option>)}
                    </select>
                    <select value={currentSequence} onChange={this.handleSequenceChange.bind(this)}>
                        <option value="all">All Sequences</option>
                        {sequences.map((sequence) => <option value={sequence.pk} key={sequence.pk}>{sequence.name}</option>)}
                    </select>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>Machine</th>
                            <th>Sequence</th>
                            <th>Date of Latest Scan</th>
                            <th>Latest Scan Within Tolerance?</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredMachineSequencePairs.map((pair) => (
                            <tr key={pair.pk}>
                                <td>{pair.machine.name}</td>
                                <td>{pair.sequence.name}</td>
                                <td>{pair.latest_scan_date && format(new Date(pair.latest_scan_date), 'MMMM D, YYYY')}</td>
                                <td>{pair.latest_scan_within_tolerance !== null && <BoolIcon value={pair.latest_scan_within_tolerance} />}</td>
                                <td><a href={pair.detail_url}>View Details</a></td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        );
    }
}

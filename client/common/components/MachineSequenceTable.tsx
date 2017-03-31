import * as React from 'react';
import { format } from 'date-fns';

import { MachineSequencePairDTO, MachineDTO, SequenceDTO } from '../service';

interface MachineSequenceTableProps {
    machineSequencePairs: MachineSequencePairDTO[];
    machines: MachineDTO[];
    sequences: SequenceDTO[];
}

interface MachineSequenceTableState {
    currentMachine: string|number;
    currentSequence: string|number;
}

export default class extends React.Component<MachineSequenceTableProps, MachineSequenceTableState> {
    constructor() {
        super();

        this.state = {
            currentMachine: 'all',
            currentSequence: 'all',
        }
    }

    filteredMachineSequencePairs() {
        const { machineSequencePairs } = this.props;
        const { currentMachine, currentSequence } = this.state;
        const filters: ((pair: MachineSequencePairDTO) => boolean)[] = [];

        if (currentMachine != 'all') {
            filters.push((pair) => pair.machine == currentMachine);
        }
        if (currentSequence != 'all') {
            filters.push((pair) => pair.sequence == currentSequence);
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
        const { machines, sequences } = this.props;
        const { currentMachine, currentSequence } = this.state;
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
                                <td>{machines.find((machine) => machine.pk === pair.machine).name}</td>
                                <td>{sequences.find((sequence) => sequence.pk === pair.sequence).name}</td>
                                <td>{pair.latest_scan_date && format(new Date(pair.latest_scan_date), 'D MMM YYYY')}</td>
                                <td>{pair.latest_scan_within_tolerance !== null && (pair.latest_scan_within_tolerance ? <i className="fa fa-check" aria-hidden="true" /> : <i className="fa fa-times" aria-hidden="true" />)}</td>
                                <td><a href={pair.detail_url}>View Details</a></td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        );
    }
}

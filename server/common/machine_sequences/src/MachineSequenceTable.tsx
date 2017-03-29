import * as React from 'react';

interface MachineSequenceTableProps {
    machineSequencePairs: MachineSequencePair[];
    machines: Machine[];
    sequences: Sequence[];
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

        let filteredMachineSequencePairs = machineSequencePairs;
        if (currentMachine != 'all') {
            filteredMachineSequencePairs = filteredMachineSequencePairs.filter((pair) => pair.machine == currentMachine);
        }
        if (currentSequence != 'all') {
            filteredMachineSequencePairs = filteredMachineSequencePairs.filter((pair) => pair.sequence == currentSequence);
        }

        return filteredMachineSequencePairs;
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
                <div className="machine-sequence-filters">
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
                                <td>{pair.latest_scan_date}</td>
                                <td>{pair.latest_scan_within_tolerance}</td>
                                <td><a href={pair.detail_url}>View Details</a></td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        );
    }
}

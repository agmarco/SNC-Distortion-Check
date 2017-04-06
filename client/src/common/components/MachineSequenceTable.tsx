import * as React from 'react';
import { format } from 'date-fns';
import uniqBy from 'lodash/uniqBy';

import { IMachineSequencePairDTO, IMachineDTO, ISequenceDTO } from '../service';
import BoolIcon from './BoolIcon';

interface IMachineSequenceTableProps {
    machineSequencePairs: IMachineSequencePairDTO[];
    uploadScanUrl: string;
}

interface IMachineSequenceTableState {
    machines: IMachineDTO[];
    sequences: ISequenceDTO[];
    currentMachinePk: string;
    currentSequencePk: string;
}

export default class extends React.Component<IMachineSequenceTableProps, IMachineSequenceTableState> {
    constructor(props: IMachineSequenceTableProps) {
        super();

        this.state = {
            machines: uniqBy(props.machineSequencePairs, (pair) => pair.machine.pk).map((pair) => pair.machine),
            sequences: uniqBy(props.machineSequencePairs, (pair) => pair.sequence.pk).map((pair) => pair.sequence),
            currentMachinePk: 'all',
            currentSequencePk: 'all',
        };
    }

    filteredMachineSequencePairs() {
        const { machineSequencePairs } = this.props;
        const { currentMachinePk, currentSequencePk } = this.state;
        const filters: Array<(pair: IMachineSequencePairDTO) => boolean> = [];

        if (currentMachinePk !== 'all') {
            filters.push((pair) => pair.machine.pk.toString() === currentMachinePk);
        }
        if (currentSequencePk !== 'all') {
            filters.push((pair) => pair.sequence.pk.toString() === currentSequencePk);
        }

        return machineSequencePairs.filter((pair) => filters.every((filter) => filter(pair)));
    }

    handleMachineChange(event: React.FormEvent<HTMLInputElement>) {
        this.setState({currentMachinePk: (event.target as any).value});
    }

    handleSequenceChange(event: React.FormEvent<HTMLInputElement>) {
        this.setState({currentSequencePk: (event.target as any).value});
    }

    render() {
        const { uploadScanUrl } = this.props;
        const { machines, sequences, currentMachinePk, currentSequencePk } = this.state;
        const filteredMachineSequencePairs = this.filteredMachineSequencePairs();

        return (
            <div>
                <a href={uploadScanUrl}>Upload New Scan</a>
                <div>
                    Filter By
                    <select value={currentMachinePk} onChange={this.handleMachineChange.bind(this)}>
                        <option value="all">All Machines</option>
                        {machines.map((machine) => (
                            <option value={machine.pk} key={machine.pk}>{machine.name}</option>
                        ))}
                    </select>
                    <select value={currentSequencePk} onChange={this.handleSequenceChange.bind(this)}>
                        <option value="all">All Sequences</option>
                        {sequences.map((sequence) => (
                            <option value={sequence.pk} key={sequence.pk}>{sequence.name}</option>
                        ))}
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
                                <td>
                                    {pair.latest_scan_date && format(new Date(pair.latest_scan_date), 'MMMM D, YYYY')}
                                </td>
                                <td>
                                    {pair.latest_scan_passed !== null && <BoolIcon value={pair.latest_scan_passed} />}
                                </td>
                                <td><a href={pair.detail_url}>View Details</a></td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        );
    }
}

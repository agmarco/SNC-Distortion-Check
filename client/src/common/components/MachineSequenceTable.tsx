import * as React from 'react';
import { format } from 'date-fns';
import uniqBy from 'lodash/uniqBy';

import { IMachineSequencePairDTO, IMachineDTO, ISequenceDTO } from '../service';
import BoolIcon from './BoolIcon';

import './MachineSequenceTable.scss';

interface IMachineSequenceTableProps {
    machineSequencePairs: IMachineSequencePairDTO[];
    uploadScanUrl: string;
}

interface IMachineSequenceTableState {
    machines: IMachineDTO[];
    sequences: ISequenceDTO[];
    machineFilterValue: 'all' | number;
    sequenceFilterValue: 'all' | number;
}

export default class extends React.Component<IMachineSequenceTableProps, IMachineSequenceTableState> {
    constructor(props: IMachineSequenceTableProps) {
        super();

        this.state = {
            machines: uniqBy(props.machineSequencePairs, (pair) => pair.machine.pk).map((pair) => pair.machine),
            sequences: uniqBy(props.machineSequencePairs, (pair) => pair.sequence.pk).map((pair) => pair.sequence),
            machineFilterValue: 'all',
            sequenceFilterValue: 'all',
        };
    }

    filteredMachineSequencePairs() {
        const { machineSequencePairs } = this.props;
        const { machineFilterValue, sequenceFilterValue } = this.state;
        const filters: Array<(pair: IMachineSequencePairDTO) => boolean> = [];

        if (machineFilterValue !== 'all') {
            filters.push((pair) => pair.machine.pk === machineFilterValue);
        }
        if (sequenceFilterValue !== 'all') {
            filters.push((pair) => pair.sequence.pk === sequenceFilterValue);
        }

        return machineSequencePairs.filter((pair) => filters.every((filter) => filter(pair)));
    }

    handleMachineChange(event: React.FormEvent<HTMLInputElement>) {
        const value = (event.target as any).value;
        this.setState({machineFilterValue: value === 'all' ? value : Number(value)});
    }

    handleSequenceChange(event: React.FormEvent<HTMLInputElement>) {
        const value = (event.target as any).value;
        this.setState({sequenceFilterValue: value === 'all' ? value : Number(value)});
    }

    render() {
        const { uploadScanUrl } = this.props;
        const { machines, sequences, machineFilterValue, sequenceFilterValue } = this.state;
        const filteredMachineSequencePairs = this.filteredMachineSequencePairs();

        return (
            <div>
                <a href={uploadScanUrl} className="btn secondary new-scan">Upload New Scan</a>
                <div className="machine-sequences-filters">
                    <span>Filter By</span>
                    <select value={machineFilterValue} onChange={this.handleMachineChange.bind(this)}>
                        <option value="all">All Machines</option>
                        {machines.map((machine) => (
                            <option value={machine.pk} key={machine.pk}>{machine.name}</option>
                        ))}
                    </select>
                    <select value={sequenceFilterValue} onChange={this.handleSequenceChange.bind(this)}>
                        <option value="all">All Sequences</option>
                        {sequences.map((sequence) => (
                            <option value={sequence.pk} key={sequence.pk}>{sequence.name}</option>
                        ))}
                    </select>
                </div>
                <table className="cirs-table">
                    <thead>
                        <tr>
                            <th>Machine</th>
                            <th>Sequence</th>
                            <th>Date of Latest Scan</th>
                            <th>Latest Scan Within Tolerance?</th>
                            <th className="sep" />
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredMachineSequencePairs.map((pair, i) => (
                            <tr key={pair.pk} className={i % 2 === 0 ? 'a' : 'b'}>
                                <td>{pair.machine.name}</td>
                                <td>{pair.sequence.name}</td>
                                <td>
                                    {pair.latest_scan_date && format(new Date(pair.latest_scan_date), 'MMMM D, YYYY')}
                                </td>
                                <td>
                                    {pair.latest_scan_passed !== null && <BoolIcon value={pair.latest_scan_passed} />}
                                </td>
                                <td className="sep" />
                                <td className="action"><a href={pair.detail_url}>View Details</a></td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        );
    }
}

import React from 'react';
import format from 'date-fns/format';
import uniqBy from 'lodash/uniqBy';

import { IMachineSequencePairDTO, IMachineDTO, ISequenceDTO } from '../service';
import BoolIcon from './BoolIcon';

import './MachineSequenceTable.scss';

export interface IMachineSequenceTableProps {
    machineSequencePairs: IMachineSequencePairDTO[];
    uploadScanUrl: string;
}

export interface IMachineSequenceTableState {
    machines: IMachineDTO[];
    sequences: ISequenceDTO[];
    machineFilterValue: 'all' | number;
    sequenceFilterValue: 'all' | number;
}

export default class extends React.Component<IMachineSequenceTableProps, IMachineSequenceTableState> {
    constructor(props: IMachineSequenceTableProps) {
        super();

        this.state = {
            machines: uniqBy(props.machineSequencePairs, p => p.machine.pk).map(p => p.machine),
            sequences: uniqBy(props.machineSequencePairs, p => p.sequence.pk).map(p => p.sequence),
            machineFilterValue: 'all',
            sequenceFilterValue: 'all',
        };
    }

    filteredMachineSequencePairs() {
        const { machineSequencePairs } = this.props;
        const { machineFilterValue, sequenceFilterValue } = this.state;
        const filters: Array<(pair: IMachineSequencePairDTO) => boolean> = [];

        if (machineFilterValue !== 'all') {
            filters.push(p => p.machine.pk === machineFilterValue);
        }
        if (sequenceFilterValue !== 'all') {
            filters.push(p => p.sequence.pk === sequenceFilterValue);
        }

        return machineSequencePairs.filter(p => filters.every(filter => filter(p)));
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
                <div className="cirs-filters">
                    <a href={uploadScanUrl} className="btn secondary new-scan">Upload New Scan</a>
                    <span>Filter By</span>
                    <select
                        className="machine-filter"
                        value={machineFilterValue}
                        onChange={this.handleMachineChange.bind(this)}
                    >
                        <option value="all">All Machines</option>
                        {machines.map(m => <option value={m.pk} key={m.pk}>{m.name}</option>)}
                    </select>
                    <select
                        className="sequence-filter"
                        value={sequenceFilterValue}
                        onChange={this.handleSequenceChange.bind(this)}
                    >
                        <option value="all">All Sequences</option>
                        {sequences.map(s => <option value={s.pk} key={s.pk}>{s.name}</option>)}
                    </select>
                </div>
                <table className="cirs-table results">
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

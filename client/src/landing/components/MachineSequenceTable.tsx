import React from 'react';
import format from 'date-fns/format';
import uniqBy from 'lodash/uniqBy';

import { IMachineSequencePairDto, IMachineDto, ISequenceDto } from 'common/service';
import { BoolIcon } from 'common/components';

import './MachineSequenceTable.scss';


export interface IMachineSequenceTableProps {
    machineSequencePairs: IMachineSequencePairDto[];
    uploadScanUrl: string;
}


export interface IMachineSequenceTableState {
    machines: IMachineDto[];
    sequences: ISequenceDto[];
    machineFilterValue: 'all' | number;
    sequenceFilterValue: 'all' | number;
}


const machineHelp = 'The name of the MRI scanner whose geometric distortion is being analyzed.';
const sequenceHelp = 'The name of the MRI sequence.  Geometric distortion is a function of both ' +
    'the particular machine, the scan sequence details, and the object being analyzed, hence distortion ' +
    'is tracked for machine-sequence combinations.';
const acquisitionDateHelp = 'The acquisition date for the latest scan on this particular machine and ' +
    'scan sequence, if present in the DICOM file, else the date when it was uploaded.';
const latestScanHelp = 'The status of the most recent scan for this machine-sequence combination.';
const latestScanFailHelp = 'The maximum distortion detected on this machine-sequence combination\'s ' +
    'then most recent scan was outside the allowed tolerance.';
const latestScanPassHelp = 'The maximum distortion detected on this machine-sequence combination\'s ' +
    'the most recent scan was within the allowed tolerance.';
const noScansAvailableHelp = 'No scans have been uploaded.';
const noScansMatchHelp = 'No scans match your current filter settings.';
const viewDetailsHelp = 'View all of the scans that have been analyzed for this machine-sequence ' +
    'combination.  Download detailed reports and diagnose errors that occurred during processing.';


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
        const filters: Array<(pair: IMachineSequencePairDto) => boolean> = [];

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
        const { uploadScanUrl, machineSequencePairs } = this.props;
        const { machines, sequences, machineFilterValue, sequenceFilterValue } = this.state;
        const noScansAvailable = machineSequencePairs.length === 0;
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
                            <th title={machineHelp}>Machine</th>
                            <th title={sequenceHelp}>Sequence</th>
                            <th title={acquisitionDateHelp}>Date of Latest Scan</th>
                            <th title={latestScanHelp}>Latest Scan Within Tolerance?</th>
                            <th className="sep" />
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredMachineSequencePairs.length > 0 ?
                            filteredMachineSequencePairs.map(machineSequenceTableRow) :
                            <tr className="empty">
                                <td colSpan={6}>
                                    {noScansAvailable ? noScansAvailableHelp : noScansMatchHelp}
                                </td>
                            </tr>
                        }
                    </tbody>
                </table>
            </div>
        );
    }
}


const machineSequenceTableRow = (pair: IMachineSequencePairDto) => {
    return (
        <tr key={pair.pk}>
            <td title={machineHelp}>{pair.machine.name}</td>
            <td title={sequenceHelp}>{pair.sequence.name}</td>
            <td title={acquisitionDateHelp}>
                {pair.latest_scan_date && format(new Date(pair.latest_scan_date), 'MMMM D, YYYY')}
            </td>
            <td>
                {pair.latest_scan_passed !== null && <BoolIcon
                    success={pair.latest_scan_passed}
                    title={pair.latest_scan_passed ? latestScanPassHelp : latestScanFailHelp}
                />}
            </td>
            <td className="sep" />
            <td className="action view-details"><a href={pair.detail_url}>View Details</a></td>
        </tr>
    );
};

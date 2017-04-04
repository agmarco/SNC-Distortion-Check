import * as React from 'react';
import { format } from 'date-fns';
import uniqBy from 'lodash/uniqBy';

import { ScanDTO, PhantomDTO } from 'common/service';
import { BoolIcon } from 'common/components'

interface ScanTableProps {
    scans: ScanDTO[];
    upload_scan_url: string;
}

interface ScanTableState {
    phantoms: PhantomDTO[];
    currentPhantomPk: string;
}

export default class extends React.Component<ScanTableProps, ScanTableState> {
    constructor(props: ScanTableProps) {
        super();

        this.state = {
            phantoms: uniqBy(props.scans, (scan) => scan.phantom.pk).map((scan) => scan.phantom),
            currentPhantomPk: 'all',
        }
    }

    filteredScans() {
        const { scans } = this.props;
        const { currentPhantomPk } = this.state;
        const filters: ((scan: ScanDTO) => boolean)[] = [];

        if (currentPhantomPk !== 'all') {
            filters.push((scan) => scan.phantom.pk.toString() == currentPhantomPk);
        }

        return scans.filter((pair) => filters.every((filter) => filter(pair)));
    }

    handlePhantomChange(event: React.FormEvent<HTMLInputElement>) {
        this.setState({currentPhantomPk: (event.target as any).value});
    }

    render() {
        const { upload_scan_url } = this.props;
        const { phantoms, currentPhantomPk } = this.state;
        const filteredScans = this.filteredScans();

        return (
            <div>
                <h2>Scans</h2>
                <a href={upload_scan_url}>Upload New Scan</a>
                <div>
                    Filter By
                    <select value={currentPhantomPk} onChange={this.handlePhantomChange.bind(this)}>
                        <option value="all">All Phantoms</option>
                        {phantoms.map((phantom) => <option value={phantom.pk} key={phantom.pk}>{phantom.model_number} &mdash; {phantom.serial_number}</option>)}
                    </select>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>Passed</th>
                            <th>Date Captured</th>
                            <th>Phantom</th>
                            <th colSpan={6}>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredScans.map((scan) => <tr key={scan.pk}>
                            <td>{!scan.processing && <BoolIcon value={scan.passed} />}</td>
                            <td>{format(scan.acquisition_date, 'MMMM D, YYYY')}</td>
                            <td>{scan.phantom.model_number} &mdash; {scan.phantom.serial_number}</td>
                            {scan.processing ? <td colSpan={6}>The Data is Still being Processed...</td> : (
                                !scan.passed ? <td colSpan={6}>There was an error while processing the data (<a href={scan.errors_url}>view details</a>)</td> : [
                                    <td key={0}><a href="#"><i className="fa fa-refresh" aria-hidden="true" /></a></td>,
                                    <td key={1}><a href="#">DICOM Overlay</a></td>,
                                    <td key={2}><a href="#">Raw Data</a></td>,
                                    <td key={3}><a href="#">Executive Report</a></td>,
                                    <td key={4}><a href="#">Full Report</a></td>,
                                    <td key={5}><a href="#"><i className="fa fa-trash-o" aria-hidden="true" /></a></td>,
                                ]
                            )}
                        </tr>)}
                    </tbody>
                </table>
            </div>
        );
    }
}

import * as React from 'react';
import { format } from 'date-fns';
import uniqBy from 'lodash/uniqBy';

import { IScanDTO, IPhantomDTO } from 'common/service';
import { BoolIcon } from 'common/components';

interface IScanTableProps {
    scans: IScanDTO[];
    uploadScanUrl: string;
}

interface IScanTableState {
    phantoms: IPhantomDTO[];
    phantomFilterValue: 'all' | number;
}

export default class extends React.Component<IScanTableProps, IScanTableState> {
    constructor(props: IScanTableProps) {
        super();

        this.state = {
            phantoms: uniqBy(props.scans, (scan) => scan.phantom.pk).map((scan) => scan.phantom),
            phantomFilterValue: 'all',
        };
    }

    filteredScans() {
        const { scans } = this.props;
        const { phantomFilterValue } = this.state;
        const filters: Array<(scan: IScanDTO) => boolean> = [];

        if (phantomFilterValue !== 'all') {
            filters.push((scan) => scan.phantom.pk === phantomFilterValue);
        }

        return scans.filter((pair) => filters.every((filter) => filter(pair)));
    }

    handlePhantomChange(event: React.FormEvent<HTMLInputElement>) {
        this.setState({phantomFilterValue: Number((event.target as any).value)});
    }

    render() {
        const { uploadScanUrl } = this.props;
        const { phantoms, phantomFilterValue } = this.state;
        const filteredScans = this.filteredScans();

        return (
            <div>
                <a href={uploadScanUrl} className="btn secondary">Upload New Scan</a>
                <div>
                    Filter By
                    <select value={phantomFilterValue} onChange={this.handlePhantomChange.bind(this)}>
                        <option value="all">All Phantoms</option>
                        {phantoms.map((phantom) => (
                            <option value={phantom.pk} key={phantom.pk}>
                                {phantom.model_number} &mdash; {phantom.serial_number}
                            </option>
                        ))}
                    </select>
                </div>
                <table className="cirs-table">
                    <thead>
                        <tr>
                            <th>Passed</th>
                            <th>Date Captured</th>
                            <th>Phantom</th>
                            <th colSpan={6}>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredScans.map((scan, i) => (
                            <tr key={scan.pk} className={i % 2 === 0 ? 'a' : 'b'}>
                                <td>{!scan.processing && !scan.errors && <BoolIcon value={scan.passed} />}</td>
                                <td>{format(scan.acquisition_date, 'MMMM D, YYYY')}</td>
                                <td>{scan.phantom.model_number} &mdash; {scan.phantom.serial_number}</td>
                                {scan.processing ? <td colSpan={6}>The Data is Still being Processed...</td> : (
                                    scan.errors ? (
                                        <td colSpan={6}>
                                            There was an error while processing the data
                                            (<a href={scan.errors_url}>view details</a>)
                                        </td>
                                        ) : [
                                        <td key={0}>
                                            <a href="#"><i className="fa fa-refresh" aria-hidden="true" /></a>
                                        </td>,
                                        <td key={1}><a href="#">DICOM Overlay</a></td>,
                                        <td key={2}><a href={scan.zipped_dicom_files_url}>Raw Data</a></td>,
                                        <td key={3}><a href="#">Executive Report</a></td>,
                                        <td key={4}><a href="#">Full Report</a></td>,
                                        <td key={5}>
                                            <a href={scan.delete_url}>
                                                <i className="fa fa-trash-o" aria-hidden="true" />
                                            </a>
                                        </td>,
                                    ]
                                )}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        );
    }
}

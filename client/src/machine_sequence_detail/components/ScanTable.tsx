import React from 'react';
import format from 'date-fns/format';
import uniqBy from 'lodash/uniqBy';

import { IScanDTO, IPhantomDTO } from 'common/service';
import { BoolIcon, CSRFToken } from 'common/components';

import './ScanTable.scss';

export interface IScanTableProps {
    scans: IScanDTO[];
    uploadScanUrl: string;
}

export interface IScanTableState {
    phantoms: IPhantomDTO[];
    phantomFilterValue: 'all' | number;
}

export default class extends React.Component<IScanTableProps, IScanTableState> {
    refreshScanForm: HTMLFormElement;

    constructor(props: IScanTableProps) {
        super();

        this.state = {
            phantoms: uniqBy(props.scans, s => s.phantom.pk).map(s => s.phantom),
            phantomFilterValue: 'all',
        };
    }

    filteredScans() {
        const { scans } = this.props;
        const { phantomFilterValue } = this.state;
        const filters: Array<(scan: IScanDTO) => boolean> = [];

        if (phantomFilterValue !== 'all') {
            filters.push(s => s.phantom.pk === phantomFilterValue);
        }

        return scans.filter(p => filters.every(filter => filter(p)));
    }

    handlePhantomChange(event: React.FormEvent<HTMLInputElement>) {
        const value = (event.target as any).value;
        this.setState({phantomFilterValue: value === 'all' ? value : Number(value)});
    }

    handleRefreshScanSubmit(event: React.FormEvent<HTMLAnchorElement>) {
        this.refreshScanForm.submit();
    }

    // TODO hook up executive report
    renderScanActions(scan: IScanDTO) {
        if (scan.processing) {
            return <td colSpan={6}>The Data is Still being Processed...</td>;
        } else if (scan.errors) {
            return (
                <td colSpan={6}>
                    <span className="error">
                        There was an error while processing the data
                        (<a href={scan.errors_url}>view details</a>)
                    </span>
                </td>
            );
        } else {
            return [
                <td key={0} className="action">
                    <form action={scan.refresh_url} method="post" ref={(e) => this.refreshScanForm = e}>
                        <CSRFToken />
                        <a href="javascript:void(0)" onClick={this.handleRefreshScanSubmit.bind(this)}>
                            <i className="fa fa-refresh" aria-hidden="true" />
                        </a>
                    </form>
                </td>,
                <td key={1} className="action">
                    <a href={scan.dicom_overlay_url}>DICOM Overlay</a>
                </td>,
                <td key={2} className="action">
                    <a href={scan.raw_data_url}>Raw Data</a>
                </td>,
                <td key={3} className="action">
                    <a href={scan.executive_report_url === null ? '#' : scan.executive_report_url}>Executive Report</a>
                </td>,
                <td key={4} className="action">
                    <a href={scan.full_report_url === null ? '#' : scan.full_report_url}>Full Report</a>
                </td>,
                <td key={5} className="action">
                    <a href={scan.delete_url}>
                        <i className="fa fa-trash-o" aria-hidden="true" />
                    </a>
                </td>,
            ];
        }
    }

    render() {
        const { uploadScanUrl } = this.props;
        const { phantoms, phantomFilterValue } = this.state;
        const filteredScans = this.filteredScans();

        return (
            <div>
                <div className="cirs-filters">
                    <a href={uploadScanUrl} className="btn secondary new-scan">Upload New Scan</a>
                    <span>Filter By</span>
                    <select
                        className="phantom-filter"
                        value={phantomFilterValue}
                        onChange={this.handlePhantomChange.bind(this)}
                    >
                        <option value="all">All Phantoms</option>
                        {phantoms.map((p) => (
                            <option value={p.pk} key={p.pk}>{p.model_number} &mdash; {p.serial_number}</option>
                        ))}
                    </select>
                </div>
                <table className="cirs-table results">
                    <thead>
                        <tr>
                            <th>Passed</th>
                            <th>Date Captured</th>
                            <th>Phantom</th>
                            <th className="sep" />
                            <th colSpan={6}>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredScans.map((scan, i) => (
                            <tr key={scan.pk} className={i % 2 === 0 ? 'a' : 'b'}>
                                <td>{scan.passed !== null && <BoolIcon value={scan.passed} />}</td>
                                <td>{format(scan.acquisition_date, 'MMMM D, YYYY')}</td>
                                <td>{scan.phantom.model_number} &mdash; {scan.phantom.serial_number}</td>
                                <td className="sep" />
                                {this.renderScanActions(scan)}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        );
    }
}

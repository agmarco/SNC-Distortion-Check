import React from 'react';
import format from 'date-fns/format';
import uniqBy from 'lodash/uniqBy';

import { IScanDto, IPhantomDto } from 'common/service';
import { BoolIcon, AnchorForm, LoadingIcon } from 'common/components';

import './ScanTable.scss';

export interface IScanTableProps {
    scans: IScanDto[];
    uploadScanUrl: string;
    pollScansError: string | null;
}

export interface IScanTableState {
    phantoms: IPhantomDto[];
    phantomFilterValue: 'all' | number;
}

const scanFailHelp = 'The maximum geometric distortion was greater than the allowed tolerance ' +
    'when the scan was analyzed.  The ROI charts in the full report may have details as to the ' +
    'cause of the failure.';
const scanPassHelp = 'The maximum geometric distortion was within the allowed tolerance ' +
    'when the scan was analyzed.';
const refreshScanHelp = 'Re-analyze this scan using the current tolerance threshold, phantom gold standard grid' +
    'intersection locations, and image processing algorithm.  The existing results remain available.';
const dicomOverlayHelp = 'Generate DICOM files to overlay the geometric distortion on another MRI.';
const rawDataHelp = 'Download a zip archive containing the raw data produced by our algorithm, which ' +
    'may be useful for debugging or independent verification.';
const executiveReportHelp = 'Download a PDF report presenting NEMA MS 12 compliant results of the ' +
    'geometric distortion analysis.';
const fullReportHelp = 'Download a detailed PDF report presenting NEMA MS 12 compliant results of the ' +
    'geometric distortion analysis with additional charts.';
const acquisitionDateHelp = 'Date when the scan was acquired if the AcquisitionDate DICOM attribute was present, ' +
    'or the date when the file was uploaded if not.';
const passedHelp = 'Was the maximum detected geometric distortion within the tolerance set at the time when ' +
    'this scan was processed?  Note if you change the tolerance, you will need to re-run the scan.';
const processingHelp = 'Processing may take several minutes. You will need to refresh the page to see updates.';

export default class extends React.Component<IScanTableProps, IScanTableState> {
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
        const filters: Array<(scan: IScanDto) => boolean> = [];

        if (phantomFilterValue !== 'all') {
            filters.push(s => s.phantom.pk === phantomFilterValue);
        }

        return scans.filter(p => filters.every(filter => filter(p)));
    }

    handlePhantomChange(event: React.FormEvent<HTMLInputElement>) {
        const value = (event.target as any).value;
        this.setState({phantomFilterValue: value === 'all' ? value : Number(value)});
    }

    renderScanActions(scan: IScanDto) {
        const { pollScansError } = this.props;

        if (scan.processing) {
            if (pollScansError) {
                return [
                    <td key={0} colSpan={5}>
                        <span className="error">
                            Something went wrong. Please refresh the page to see if the scan has finished processing.
                        </span>
                    </td>,
                    <td key={1} className="action delete">
                        <a href={scan.delete_url}>
                            <i className="fa fa-trash-o" aria-hidden="true" />
                        </a>
                    </td>,
                ];
            } else {
                return [
                    <td key={0} colSpan={5} title={processingHelp}>
                        The data is still being processed...
                        {' '}
                        <LoadingIcon />
                    </td>,
                    <td key={1} className="action delete">
                        <a href={scan.delete_url}>
                            <i className="fa fa-trash-o" aria-hidden="true" />
                        </a>
                    </td>,
                ];
            }
        } else if (scan.errors) {
            return [
                <td key={0} colSpan={5}>
                    <span className="error">
                        There was an error while processing the data
                        (<a href={scan.errors_url}>view details</a>).
                    </span>
                </td>,
                <td key={1} className="action delete">
                    <a href={scan.delete_url}>
                        <i className="fa fa-trash-o" aria-hidden="true" />
                    </a>
                </td>,
            ];
        } else {
            return [
                <td key={0} className="action refresh-scan" title={refreshScanHelp}>
                    <AnchorForm action={scan.refresh_url}>
                        <i className="fa fa-refresh" aria-hidden="true" />
                    </AnchorForm>
                </td>,
                <td key={1} className="action dicom-overlay" title={dicomOverlayHelp}>
                    <a href={scan.dicom_overlay_url}>DICOM Overlay</a>
                </td>,
                <td key={2} className="action raw-data" title={rawDataHelp}>
                    <a href={scan.raw_data_url}>Raw Data</a>
                </td>,
                <td key={3} className="action executive-report" title={executiveReportHelp}>
                    <a href={scan.executive_report_url === null ? '#' : scan.executive_report_url}>Executive Report</a>
                </td>,
                <td key={4} className="action full-report" title={fullReportHelp}>
                    <a href={scan.full_report_url === null ? '#' : scan.full_report_url}>Full Report</a>
                </td>,
                <td key={5} className="action delete">
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
                            <th title={passedHelp}>Passed</th>
                            <th title={acquisitionDateHelp}>Date Captured</th>
                            <th>Phantom</th>
                            <th className="sep" />
                            <th colSpan={6}>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredScans.map((scan, i) => (
                            <tr key={scan.pk}>
                                <td title={scan.passed ? scanPassHelp : scanFailHelp}>
                                    {scan.passed !== null && <BoolIcon success={scan.passed} />}
                                </td>
                                <td title={acquisitionDateHelp}>{format(scan.acquisition_date, 'MMMM D, YYYY')}</td>
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

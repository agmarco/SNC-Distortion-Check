import * as React from 'react';
import { format } from 'date-fns';

import { ScanDTO } from 'common/service';
import { BoolIcon } from 'common/components'

interface ScanTableProps {
    scans: ScanDTO[];
    upload_scan_url: string;
}

export default class extends React.Component<ScanTableProps, {}> {
    render() {
        const { scans, upload_scan_url } = this.props;

        return (
            <div>
                <h2>Scans</h2>
                <a href={upload_scan_url}>Upload New Scan</a>
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
                        {scans.map((scan) => <tr key={scan.pk}>
                            <td>{!scan.processing && <BoolIcon value={!scan.errors} />}</td>
                            <td>{format(scan.acquisition_date, 'MMMM D, YYYY')}</td>
                            <td>{scan.phantom_summary}</td>
                            {scan.processing ? <td colSpan={6}>The Data is Still being Processed...</td> : (
                                scan.errors ? <td colSpan={6}>There was an error while processing the data (view details)</td> : [
                                <td key={0}>Refresh</td>,
                                <td key={1}>DICOM Overlay</td>,
                                <td key={2}>Raw Data</td>,
                                <td key={3}>Executive Report</td>,
                                <td key={4}>Full Report</td>,
                                <td key={5}>Delete</td>,
                            ])}
                        </tr>)}
                    </tbody>
                </table>
            </div>
        );
    }
}

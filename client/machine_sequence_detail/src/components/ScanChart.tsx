import * as React from 'react';

import { ScanDTO } from 'common/service';

interface ScanChartProps {
    scans: ScanDTO[];
}

export default class extends React.Component<ScanChartProps, {}> {
    render() {
        const { scans } = this.props;

        return (
            <div>
                <h2>Performance over Time</h2>
            </div>
        );
    }
}

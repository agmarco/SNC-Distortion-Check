import * as React from 'react';

interface MachineSequenceTableProps {
    machineSequencePairs: MachineSequencePair[];
    machines: Machine[];
    sequences: Sequence[];
}

export default class extends React.Component<MachineSequenceTableProps, {}> {
    render() {
        const { machineSequencePairs, machines, sequences } = this.props;
        return (
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
                    {machineSequencePairs.map((pair) => (
                        <tr key={pair.pk}>
                            <td>{machines.find((machine) => machine.pk === pair.machine).name}</td>
                            <td>{sequences.find((sequence) => sequence.pk === pair.sequence).name}</td>
                            <td>{pair.latest_scan_date}</td>
                            <td>{pair.latest_scan_within_tolerance}</td>
                            <td><a href={pair.detail_url}>View Details</a></td>
                        </tr>
                    ))}
                </tbody>
            </table>
        );
    }
}

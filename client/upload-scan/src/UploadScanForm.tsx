import * as React from 'react';
import { Machine, Sequence, Phantom} from 'cirs-common';

interface UploadScanFormProps {
    machines: Machine[];
    sequences: Sequence[];
    phantoms: Phantom[];
}

interface UploadScanFormState {
    machine: number;
    sequence: number;
    phantom: number;
}

export default class extends React.Component<UploadScanFormProps, UploadScanFormState> {
    render() {
        return (
            <div>
            </div>
        );
    }
}

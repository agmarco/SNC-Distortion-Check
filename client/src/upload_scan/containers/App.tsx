import React from 'react';

import { IMachineDTO, ISequenceDTO, IPhantomDTO } from 'common/service';
import UploadScanForm from '../components/UploadScanForm';

declare const MACHINES: IMachineDTO[];
declare const SEQUENCES: ISequenceDTO[];
declare const PHANTOMS: IPhantomDTO[];
declare const UPLOAD_SCAN_URL: string;
declare const CANCEL_URL: string;
declare const FORM_ERRORS: {[field: string]: string[]};

export default () => (
    <div>
        <h1>Upload Scan</h1>
        <UploadScanForm
            machines={MACHINES}
            sequences={SEQUENCES}
            phantoms={PHANTOMS}
            uploadScanUrl={UPLOAD_SCAN_URL}
            cancelUrl={CANCEL_URL}
            formErrors={FORM_ERRORS}
        />
    </div>
);

import React from 'react';

import { IMachineDTO, ISequenceDTO, IPhantomDTO } from 'common/service';
import UploadScanForm from '../components/UploadScanForm';

declare const MACHINES: IMachineDTO[];
declare const SEQUENCES: ISequenceDTO[];
declare const PHANTOMS: IPhantomDTO[];
declare const INITIAL_MACHINE_PK: number | null;
declare const INITIAL_SEQUENCE_PK: number | null;
declare const CANCEL_URL: string;
declare const FORM_ERRORS: {[field: string]: string[]};

export default () => (
    <div>
        <h1>Upload Scan</h1>
        <UploadScanForm
            machines={MACHINES}
            sequences={SEQUENCES}
            phantoms={PHANTOMS}
            initialMachinePk={INITIAL_MACHINE_PK}
            initialSequencePk={INITIAL_SEQUENCE_PK}
            cancelUrl={CANCEL_URL}
            formErrors={FORM_ERRORS}
        />
    </div>
);

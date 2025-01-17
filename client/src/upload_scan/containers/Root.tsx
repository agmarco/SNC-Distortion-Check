import React from 'react';

import { IDjangoFormErrors } from 'common/forms';
import { IMachineDto, ISequenceDto, IPhantomDto } from 'common/service';
import UploadScanForm from '../components/UploadScanForm';

declare const MACHINES: IMachineDto[];
declare const SEQUENCES: ISequenceDto[];
declare const PHANTOMS: IPhantomDto[];
declare const INITIAL_MACHINE_PK: number | null;
declare const INITIAL_SEQUENCE_PK: number | null;
declare const CANCEL_URL: string;
declare const FORM_ACTION: string;
declare const FORM_ERRORS: IDjangoFormErrors;

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
            formAction={FORM_ACTION}
            formErrors={FORM_ERRORS}
        />
    </div>
);

import * as React from 'react';
import * as Cookies from 'js-cookie';

import { MachineDTO, SequenceDTO, PhantomDTO } from 'common/service';
import UploadScanForm from 'components/UploadScanForm';

declare const MACHINES: MachineDTO[];
declare const SEQUENCES: SequenceDTO[];
declare const PHANTOMS: PhantomDTO[];
declare const UPLOAD_SCAN_URL: string;
declare const CANCEL_URL: string;
declare const FORM_ERRORS: {[field: string]: string[]};

export default () => (
    <UploadScanForm
        machines={MACHINES}
        sequences={SEQUENCES}
        phantoms={PHANTOMS}
        upload_scan_url={UPLOAD_SCAN_URL}
        cancel_url={CANCEL_URL}
        form_errors={FORM_ERRORS}
        csrftoken={Cookies.get('csrftoken')}
    />
);

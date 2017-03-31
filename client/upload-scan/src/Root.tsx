import * as React from 'react';
import * as Cookies from 'js-cookie';
import { AppContainer } from 'react-hot-loader';

import { MachineDTO, SequenceDTO, PhantomDTO } from 'common/service';
import UploadScanForm from './components/UploadScanForm';

declare const __MACHINES__: MachineDTO[];
declare const __SEQUENCES__: SequenceDTO[];
declare const __PHANTOMS__: PhantomDTO[];
declare const __UPLOAD_SCAN_URL__: string;
declare const __CANCEL_URL__: string;
declare const __FORM_ERRORS__: {[field: string]: string[]};

export default () => (
    <AppContainer>
        <UploadScanForm
            machines={__MACHINES__}
            sequences={__SEQUENCES__}
            phantoms={__PHANTOMS__}
            upload_scan_url={__UPLOAD_SCAN_URL__}
            cancel_url={__CANCEL_URL__}
            form_errors={__FORM_ERRORS__}
            csrftoken={Cookies.get('csrftoken')}
        />
    </AppContainer>
);

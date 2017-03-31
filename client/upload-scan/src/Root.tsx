import * as React from 'react';
import { AppContainer } from 'react-hot-loader';
import { Machine, Sequence, Phantom } from 'cirs-common';

import UploadScanForm from './UploadScanForm';

declare const __MACHINES__: Machine[];
declare const __SEQUENCES__: Sequence[];
declare const __PHANTOMS__: Phantom[];

export default () => (
    <AppContainer>
        <UploadScanForm
            machines={__MACHINES__}
            sequences={__SEQUENCES__}
            phantoms={__PHANTOMS__}
        />
    </AppContainer>
);

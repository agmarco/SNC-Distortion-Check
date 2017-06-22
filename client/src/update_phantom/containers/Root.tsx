import React from 'react';

import { IDjangoFormErrors } from 'common/forms';
import { IPhantomDto, IGoldenFiducialsDto } from 'common/service';
import { IUpdatePhantomForm } from '../forms';
import UpdatePhantomForm from '../components/UpdatePhantomForm';
import GoldStandardTable from '../components/GoldStandardTable';

declare const FORM_INITIAL: IUpdatePhantomForm | null;
declare const FORM_ERRORS: IDjangoFormErrors;
declare const FORM_ACTION: string;
declare const PHANTOM: IPhantomDto;

export default () => (
    <div>
        <h1>Edit Phantom</h1>
        <UpdatePhantomForm
            formErrors={FORM_ERRORS}
            formAction={FORM_ACTION}
        />
        <GoldStandardTable
            phantom={PHANTOM}
        />
    </div>
);

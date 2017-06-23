import React from 'react';

import { IDjangoFormErrors } from 'common/forms';
import { IPhantomDto } from 'common/service';
import UpdatePhantomForm from '../components/UpdatePhantomForm';
import GoldStandardTable from '../components/GoldStandardTable';


export declare const FORM_ACTION: string;
export declare const FORM_ERRORS: IDjangoFormErrors;
export declare const PHANTOM: IPhantomDto;


export default () => (
    <div>
        <h1>Edit Phantom</h1>
        <UpdatePhantomForm
            formAction={FORM_ACTION}
            formErrors={FORM_ERRORS}
        />
        <GoldStandardTable
            phantom={PHANTOM}
        />
    </div>
);

import { IDjangoFormErrors } from 'common/forms';
import { IMachineDto, ISequenceDto, IPhantomDto } from 'common/service';
import { IUploadScanForm } from './forms';

export declare const MACHINES: IMachineDto[];
export declare const SEQUENCES: ISequenceDto[];
export declare const PHANTOMS: IPhantomDto[];
export declare const INITIAL_MACHINE_PK: number | null;
export declare const INITIAL_SEQUENCE_PK: number | null;
export declare const CANCEL_URL: string;
export declare const FORM_ACTION: string;
export declare const FORM_INITIAL: IUploadScanForm;
export declare const FORM_ERRORS: IDjangoFormErrors;

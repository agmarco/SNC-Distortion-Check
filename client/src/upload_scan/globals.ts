import { IDjangoFormErrors } from 'common/forms';
import { IMachineDto, ISequenceDto, IPhantomDto } from 'common/service';
import { IUploadScanForm } from './forms';

declare const MACHINES: IMachineDto[];
declare const SEQUENCES: ISequenceDto[];
declare const PHANTOMS: IPhantomDto[];
declare const INITIAL_MACHINE_PK: number | null;
declare const INITIAL_SEQUENCE_PK: number | null;
declare const CANCEL_URL: string;
declare const FORM_ACTION: string;
declare const FORM_INITIAL: IUploadScanForm;
declare const FORM_ERRORS: IDjangoFormErrors;

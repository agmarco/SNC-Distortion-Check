import { IDjangoFormErrors } from 'common/forms';
import { IPhantomDto, IGoldenFiducialsDto } from 'common/service';
import { IUpdatePhantomForm } from './forms';

declare const FORM_ACTION: string;
declare const FORM_INITIAL: IUpdatePhantomForm;
declare const FORM_ERRORS: IDjangoFormErrors;
declare const PHANTOM: IPhantomDto;
declare const GOLDEN_FIDUCIALS_SET: IGoldenFiducialsDto[];
declare const POLL_CT_URL: string;

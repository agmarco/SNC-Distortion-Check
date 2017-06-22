import { combineForms } from 'react-redux-form';

import { ICreatePhantomForm } from './forms';

declare const FORM_INITIAL: ICreatePhantomForm;

export default combineForms({
    phantom: FORM_INITIAL,
});

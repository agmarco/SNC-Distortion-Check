import { combineForms } from 'react-redux-form';

import { IRegisterForm } from './forms';

declare const FORM_INITIAL: IRegisterForm;

export default combineForms({
    register: FORM_INITIAL,
});

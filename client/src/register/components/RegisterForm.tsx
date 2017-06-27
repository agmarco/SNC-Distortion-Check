import React from 'react';
import { connect } from 'react-redux';
import { FieldState } from 'react-redux-form';
import { Dispatch } from 'redux';

import { CSRFToken } from 'common/components';
import { CirsForm, CirsControl, CirsErrors, IDjangoFormErrors } from 'common/forms';
import { IRegisterForm } from '../forms';
import * as actions from '../actions';
import { IAppState, ISerialNumberInfoState } from '../reducers';

interface IRegisterFormProps {
    cancelUrl: string;
    formErrors: IDjangoFormErrors | null;
    formAction: string;
    form?: IRegisterForm;
    formState?: { [name: string]: FieldState };
    dispatch?: Dispatch<any>;
    serialNumberInfo?: ISerialNumberInfoState;
}

class RegisterForm extends React.Component<IRegisterFormProps, {}> {
    componentDidMount() {
        const { form } = this.props;

        if (form) {
            this.validateSerialNumber({target: {value: form.phantom_serial_number}});
        }
    }

    validateSerialNumber(event: any) {
        const { dispatch } = this.props;

        if (dispatch) {
            dispatch(actions.validateSerialNumber((event.target as any).value));
        }
    }

    render() {
        const { cancelUrl, formErrors, formAction, formState, form, serialNumberInfo } = this.props;
        const { message, modelNumber} = serialNumberInfo as ISerialNumberInfoState;
        const { pristine, validating, valid } = (formState as { [name: string]: FieldState }).phantom_serial_number;
        const cirs603AUrl = 'http://www.cirsinc.com/products/all/99/mri-distortion-phantom-for-srs/';
        const cirs604Url = 'http://www.cirsinc.com/products/all/118/large-field-mri-distortion-phantom/';

        let modelNumberText = null;
        if (!pristine || (form && form.phantom_serial_number !== '')) {
            if (validating) {
                modelNumberText = "Searching...";
            } else if (valid) {
                modelNumberText = <span className="success">{modelNumber}</span>;
            } else {
                modelNumberText = <span className="error">{message}</span>;
            }
        }

        return (
            <div>
                <CirsForm
                    action={formAction}
                    method="post"
                    model="forms.register"
                    className="cirs-form"
                    djangoErrors={formErrors}
                >

                    {/* TODO global errors aren't showing */}
                    <CirsControl type="hidden" model=".__all__" />
                    <CirsErrors model=".__all__" />

                    <CSRFToken />

                    <p>
                        In order to registerd a new account, you must provide the serial number of
                        a <a href={cirs603AUrl}>CIRS 603A</a> or <a href={cirs604Url}>CIRS 604</a> phantom. If you
                        have not puchased either of these phantoms, but would like to know more about the Distortion
                        Check software,
                        please <a href="http://www.cirsinc.com/support/contact">contact CIRS support</a> for more
                        information.
                    </p>
                    <p>
                        You will be able to register additional phantoms once you have created your account.
                    </p>

                    <div>
                        <label htmlFor="register-phantom-serial-number">Phantom Serial Number</label>
                        <CirsControl.text
                            id="register-phantom-serial-number"
                            model=".phantom_serial_number"
                            onChange={this.validateSerialNumber.bind(this)}
                            required
                        />
                        {/* <CirsErrors model=".phantom_serial_number" required /> */}
                    </div>

                    <div>
                        <label>Model Number</label>
                        <p>{modelNumberText}</p>
                    </div>

                    <p>
                        Please provide the following details about the institution that purchased the phantom. If there
                        are any issues registering the account, a CIRS representative will contact you at the
                        institution phone number your provide.
                    </p>

                    <div>
                        <label htmlFor="register-institution-name">Institution Name</label>
                        <CirsControl.text
                            model=".institution_name"
                            id="register-institution-name"
                            required
                        />
                        <CirsErrors model=".institution_name" required />
                    </div>

                    <div>
                        <label htmlFor="register-institution-address">Institution Address</label>
                        <CirsControl.textarea
                            id="register-institution-address"
                            model=".institution_address"
                            cols={40}
                            rows={10}
                            required
                        />
                        <CirsErrors model=".institution_address" required />
                    </div>

                    <div>
                        <label htmlFor="register-institution-phone">Institution Contact Phone Number</label>
                        <CirsControl.text
                            model=".institution_phone"
                            id="register-institution-phone"
                            required
                        />
                        <CirsErrors model=".institution_phone" required />
                    </div>

                    <p>The following details will be used to setup a default admin user account.</p>

                    <div>
                        <label htmlFor="register-first-name">First Name</label>
                        <CirsControl.text
                            model=".first_name"
                            id="register-first-name"
                            required
                        />
                        <CirsErrors model=".first_name" required />
                    </div>

                    <div>
                        <label htmlFor="register-last-name">Last Name</label>
                        <CirsControl.text
                            model=".last_name"
                            id="register-last-name"
                            required
                        />
                        <CirsErrors model=".last_name" required />
                    </div>

                    <div>
                        <label htmlFor="register-email">Email</label>
                        <CirsControl.input
                            model=".email"
                            type="email"
                            id="register-email"
                            required
                        />
                        <CirsErrors model=".email" required email />
                    </div>

                    <div>
                        <label htmlFor="register-email-repeat">Email Repeat</label>
                        <CirsControl.input
                            model=".email_repeat"
                            type="email"
                            id="register-email-repeat"
                            required
                        />
                        <CirsErrors model=".email_repeat" required email />
                    </div>

                    <div className="form-links">
                        <a href={cancelUrl} className="btn tertiary">Cancel</a>
                        <input
                            type="submit"
                            value="Register"
                            disabled={validating || !valid}
                            className="btn secondary"
                        />
                    </div>
                </CirsForm>
            </div>
        );
    }
}
export default connect<any, any, any>((state: IAppState) => ({
    form: state.forms.register,
    formState: state.forms.forms.register,
    serialNumberInfo: state.serialNumberInfo,
}))(RegisterForm as any);

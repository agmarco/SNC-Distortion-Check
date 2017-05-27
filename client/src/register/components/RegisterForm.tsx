import React from 'react';
import * as Cookies from 'js-cookie';
import * as Bluebird from 'bluebird';
import { connect } from 'react-redux';
import { FieldState } from 'react-redux-form';

import { handleErrors, encode } from 'common/utils';
import { CSRFToken } from 'common/components';
import { CIRSForm, CIRSControl, CIRSErrors, IDjangoFormData, IDjangoFormErrors } from 'common/forms';

interface IRegisterFormProps {
    validateSerialUrl: string;
    cancelUrl: string;
    formData: IDjangoFormData;
    formErrors: IDjangoFormErrors;
    formAction: string;
    formState?: { [name: string]: FieldState };
}

interface IRegisterFormState {
    serialNumberMessage: string | null;
    modelNumber: string | null;
    promise: Bluebird<any> | null;
}

class RegisterForm extends React.Component<IRegisterFormProps, IRegisterFormState> {
    constructor() {
        super();

        Bluebird.config({cancellation: true});
        this.state = {
            serialNumberMessage: null,
            modelNumber: null,
            promise: null,
        };
    }

    validateSerialNumber(value: string, done: Function) {
        const { validateSerialUrl } = this.props;
        const { promise } = this.state;

        if (promise) {
            promise.cancel();
        }

        const newPromise = Bluebird.resolve(fetch(validateSerialUrl, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': Cookies.get('csrftoken'),
                },
                body: encode({serial_number: value}),
            }))
            .then((res) => {
                handleErrors(res, (async function() {
                    const { valid, model_number, message } = await res.json();

                    this.setState({
                        serialNumberMessage: message,
                        modelNumber: model_number,
                        promise: null,
                    });
                    done(valid);
                }).bind(this));
            });

        this.setState({
            serialNumberMessage: null,
            modelNumber: null,
            promise: newPromise,
        });
    }

    render() {
        const { cancelUrl, formData, formErrors, formAction, formState } = this.props;
        const { serialNumberMessage, modelNumber } = this.state;
        const { pristine, validating, valid } = (formState as { [name: string]: FieldState }).phantom_serial_number;
        const cirs603AUrl = 'http://www.cirsinc.com/products/all/99/mri-distortion-phantom-for-srs/';
        const cirs604Url = 'http://www.cirsinc.com/products/all/118/large-field-mri-distortion-phantom/';

        let modelNumberText = null;
        if (!pristine) {
            if (validating) {
                modelNumberText = "Searching...";
            } else if (valid) {
                modelNumberText = <span className="success">{modelNumber}</span>;
            } else {
                modelNumberText = <span className="error">{serialNumberMessage}</span>;
            }
        }

        return (
            <div>
                <CIRSErrors model="register" />

                <CIRSForm
                    action={formAction}
                    method="post"
                    model="register"
                    className="cirs-form"
                    djangoData={formData}
                    djangoErrors={formErrors}
                >
                    <CSRFToken />

                    <p>
                        In order to registerd a new account, you must provide the serial number of
                        your <a href={cirs603AUrl}>CIRS 603A</a> or <a href={cirs604Url}>CIRS 604</a> phantom. If you
                        have not puchased either of these phantoms, but would like to know more about the Distortion
                        Check software,
                        please <a href="http://www.cirsinc.com/support/contact">contact CIRS support</a> for more
                        information.
                    </p>

                    {/* TODO async validation messed up when value is already populated */}
                    <div>
                        <label htmlFor="register-phantom-serial-number">Phantom Serial Number</label>
                        <CIRSControl.text
                            id="register-phantom-serial-number"
                            model=".phantom_serial_number"
                            asyncValidators={{valid: this.validateSerialNumber.bind(this)}}
                            asyncValidateOn="change"
                            required
                        />
                        <CIRSErrors model=".phantom_serial_number" />
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
                        <CIRSControl.text
                            model=".institution_name"
                            id="register-institution-name"
                            required
                        />
                        <CIRSErrors model=".institution_name" />
                    </div>

                    <div>
                        <label htmlFor="register-institution-address">Institution Address</label>
                        <CIRSControl.textarea
                            id="register-institution-address"
                            model=".institution_address"
                            cols={40}
                            rows={10}
                            required
                        />
                        <CIRSErrors model=".institution_address" />
                    </div>

                    <div>
                        <label htmlFor="register-institution-phone">Institution Contact Phone Number</label>
                        <CIRSControl.text
                            model=".institution_phone"
                            id="register-institution-phone"
                            required
                        />
                        <CIRSErrors model=".institution_phone" />
                    </div>

                    <p>The following details will be used to setup a default admin user account.</p>

                    <div>
                        <label htmlFor="register-first-name">First Name</label>
                        <CIRSControl.text
                            model=".first_name"
                            id="register-first-name"
                            required
                        />
                        <CIRSErrors model=".first_name" />
                    </div>

                    <div>
                        <label htmlFor="register-last-name">Last Name</label>
                        <CIRSControl.text
                            model=".last_name"
                            id="register-last-name"
                            required
                        />
                        <CIRSErrors model=".last_name" />
                    </div>

                    <div>
                        <label htmlFor="register-email">Email</label>
                        <CIRSControl.input
                            model=".email"
                            type="email"
                            id="register-email"
                            required
                        />
                        <CIRSErrors model=".email" />
                    </div>

                    <div>
                        <label htmlFor="register-email-repeat">Email Repeat</label>
                        <CIRSControl.input
                            model=".email_repeat"
                            type="email"
                            id="register-email-repeat"
                            required
                        />
                        <CIRSErrors model=".email_repeat" />
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
                </CIRSForm>
            </div>
        );
    }
}

export default connect<any, any, any>((state: any) => ({formState: state.forms.register}))(RegisterForm as any);

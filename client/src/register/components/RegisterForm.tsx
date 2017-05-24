import React from 'react';
import * as Cookies from 'js-cookie';
import * as Bluebird from 'bluebird';

import { handleErrors, encode, fieldErrors } from 'common/utils';
import { CSRFToken } from 'common/components';

interface IRegisterFormProps {
    validateSerialUrl: string;
    cancelUrl: string;
    formErrors: {[field: string]: string[]};
}

interface IRegisterFormState {
    serialNumberPristine: boolean;
    serialNumberFetching: boolean;
    serialNumberValid: boolean;
    serialNumberMessage: string | null;
    modelNumber: string | null;
    promise: Bluebird<any> | null;
}

export default class extends React.Component<IRegisterFormProps, IRegisterFormState> {
    constructor() {
        super();

        Bluebird.config({cancellation: true});
        this.state = {
            serialNumberPristine: true,
            serialNumberFetching: false,
            serialNumberValid: false,
            serialNumberMessage: null,
            modelNumber: null,
            promise: null,
        };
    }

    handleSerialChange(event: React.FormEvent<HTMLInputElement>) {
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
                body: encode({serial_number: (event.target as any).value}),
            }))
            .then((res) => {
                handleErrors(res, (async function() {
                    const { valid, model_number, message } = await res.json();

                    this.setState({
                        serialNumberFetching: false,
                        serialNumberValid: valid,
                        serialNumberMessage: message,
                        modelNumber: model_number,
                        promise: null,
                    });
                }).bind(this));
            });

        this.setState({
            serialNumberPristine: false,
            serialNumberFetching: true,
            serialNumberValid: false,
            serialNumberMessage: null,
            modelNumber: null,
            promise: newPromise,
        });
    }

    render() {
        const { cancelUrl, formErrors } = this.props;
        const {
            serialNumberPristine,
            serialNumberFetching,
            serialNumberValid,
            serialNumberMessage,
            modelNumber,
        } = this.state;
        const cirs603AUrl = 'http://www.cirsinc.com/products/all/99/mri-distortion-phantom-for-srs/';
        const cirs604Url = 'http://www.cirsinc.com/products/all/118/large-field-mri-distortion-phantom/';

        let modelNumberText = null;
        if (!serialNumberPristine) {
            if (serialNumberFetching) {
                modelNumberText = "Searching...";
            } else if (serialNumberValid) {
                modelNumberText = <span className="success">{modelNumber}</span>;
            } else {
                modelNumberText = <span className="error">{serialNumberMessage}</span>;
            }
        }

        return (
            <div>
                <form method="post" className="cirs-form">
                    <CSRFToken />

                    {fieldErrors(formErrors, '__all__')}

                    <p>
                        In order to registerd a new account, you must provide the serial number of
                        your <a href={cirs603AUrl}>CIRS 603A</a> or <a href={cirs604Url}>CIRS 604</a> phantom. If you
                        have not puchased either of these phantoms, but would like to know more about the Distortion
                        Check software,
                        please <a href="http://www.cirsinc.com/support/contact">contact CIRS support</a> for more
                        information.
                    </p>

                    <div>
                        <label htmlFor="register-phantom-serial-number">Phantom Serial Number</label>
                        <input
                            type="text"
                            id="register-phantom-serial-number"
                            name="phantom_serial_number"
                            maxLength={255}
                            onChange={this.handleSerialChange.bind(this)}
                            required
                        />
                        {fieldErrors(formErrors, 'phantom_serial_number')}
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
                        <input
                            type="text"
                            id="register-institution-name"
                            name="institution_name"
                            maxLength={255}
                            required
                        />
                        {fieldErrors(formErrors, 'institution_name')}
                    </div>

                    <div>
                        <label htmlFor="register-institution-address">Institution Address</label>
                        <textarea
                            id="register-institution-name"
                            name="institution_address"
                            cols={40}
                            rows={10}
                            required
                        />
                        {fieldErrors(formErrors, 'institution_address')}
                    </div>

                    <div>
                        <label htmlFor="register-institution-phone">Institution Contact Phone Number</label>
                        <input
                            type="text"
                            id="register-institution-phone"
                            name="institution_phone"
                            maxLength={255}
                            required
                        />
                        {fieldErrors(formErrors, 'institution_phone')}
                    </div>

                    <p>The following details will be used to setup a default admin user account.</p>

                    <div>
                        <label htmlFor="register-first-name">First Name</label>
                        <input
                            type="text"
                            id="register-first-name"
                            name="first_name"
                            maxLength={255}
                            required
                        />
                        {fieldErrors(formErrors, 'first_name')}
                    </div>

                    <div>
                        <label htmlFor="register-last-name">Last Name</label>
                        <input
                            type="text"
                            id="register-last-name"
                            name="last_name"
                            maxLength={255}
                            required
                        />
                        {fieldErrors(formErrors, 'last_name')}
                    </div>

                    <div>
                        <label htmlFor="register-email">Email</label>
                        <input
                            type="email"
                            id="register-email"
                            name="email"
                            maxLength={255}
                            required
                        />
                        {fieldErrors(formErrors, 'email')}
                    </div>

                    <div>
                        <label htmlFor="register-email-repeat">Email Repeat</label>
                        <input
                            type="email"
                            id="register-email-repeat"
                            name="email_repeat"
                            maxLength={255}
                            required
                        />
                        {fieldErrors(formErrors, 'email_repeat')}
                    </div>

                    <div className="form-links">
                        <a href={cancelUrl} className="btn tertiary">Cancel</a>
                        <input
                            type="submit"
                            value="Register"
                            disabled={serialNumberFetching || !serialNumberValid}
                            className="btn secondary"
                        />
                    </div>
                </form>
            </div>
        );
    }
}

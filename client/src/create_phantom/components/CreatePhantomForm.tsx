import React from 'react';
import * as Cookies from 'js-cookie';
import * as Bluebird from 'bluebird';
import { Dispatch } from 'redux';
import { connect } from 'react-redux';
import { FieldState, actions } from 'react-redux-form';

import { handleErrors, encode } from 'common/utils';
import { CirsForm, CirsControl, CirsErrors, IDjangoFormData, IDjangoFormErrors } from 'common/forms';
import { CSRFToken } from 'common/components';

interface ICreatePhantomFormProps {
    validateSerialUrl: string;
    cancelUrl: string;
    formData: IDjangoFormData | null;
    formErrors: IDjangoFormErrors | null;
    formAction: string;
    formState?: { [name: string]: FieldState };
    dispatch?: Dispatch<any>;
}

interface ICreatePhantomFormState {
    serialNumberMessage: string | null;
    modelNumber: string | null;
    promise: Bluebird<any> | null;
}

class CreatePhantomForm extends React.Component<ICreatePhantomFormProps, ICreatePhantomFormState> {
    constructor() {
        super();

        Bluebird.config({cancellation: true});
        this.state = {
            serialNumberMessage: null,
            modelNumber: null,
            promise: null,
        };
    }

    validateSerialNumber(event: any) {
        const { validateSerialUrl, dispatch } = this.props;
        const { promise } = this.state;

        if (promise) {
            promise.cancel();
        }

        // TODO redux-saga?
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
                        serialNumberMessage: message,
                        modelNumber: model_number,
                        promise: null,
                    });

                    if (dispatch) {
                        dispatch(actions.setValidity('phantom.serial_number', valid));
                    }
                }).bind(this));
            });

        this.setState({
            serialNumberMessage: null,
            modelNumber: null,
            promise: newPromise,
        });
    }

    render() {
        const { cancelUrl, formState, formAction, formData, formErrors } = this.props;
        const { serialNumberMessage, modelNumber} = this.state;
        const { pristine, validating, valid } = (formState as { [name: string]: FieldState }).serial_number;

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
                <CirsForm
                    action={formAction}
                    method="post"
                    model="phantom"
                    className="cirs-form"
                    djangoData={formData}
                    djangoErrors={formErrors}
                >
                    <CirsControl type="hidden" model="._" />
                    <CirsErrors model="._" />

                    <CSRFToken />

                    <div>
                        <label htmlFor="phantom-name">Name</label>
                        <CirsControl.text id="phantom-name" model=".name" required />
                        <CirsErrors model=".name" required />
                    </div>

                    <div>
                        <label htmlFor="phantom-serial-number">Serial Number</label>
                        <CirsControl.text
                            id="phantom-serial-number"
                            model=".serial_number"
                            onChange={this.validateSerialNumber.bind(this)}
                            required
                        />
                        {/*<CirsErrors model=".serial_number" required />*/}
                    </div>

                    <div>
                        <label>Model Number</label>
                        <p>{modelNumberText}</p>
                    </div>

                    <div>
                        <label>Gold Standard Grid Intersection Locations</label>
                        <p>
                            By default, the new phantom will use gold standard grid intersection locations based on the
                            CAD design for the particular phantom model you select. These points can be customized at
                            any point using a gold standard CT, or a raw point upload.
                        </p>
                    </div>

                    <div className="form-links">
                        <a href={cancelUrl} className="btn tertiary">Cancel</a>
                        <input
                            type="submit"
                            value="Add Phantom"
                            disabled={validating || !valid}
                            className="btn secondary"
                        />
                    </div>
                </CirsForm>
            </div>
        );
    }
}

// TODO figure out the types
export default connect<any, any, any>((state: any) => ({formState: state.forms.phantom}))(CreatePhantomForm as any);

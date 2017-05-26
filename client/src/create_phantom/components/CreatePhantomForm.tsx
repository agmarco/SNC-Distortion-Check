import React from 'react';
import * as Cookies from 'js-cookie';
import * as Bluebird from 'bluebird';
import { Dispatch } from 'redux';
import { connect } from 'react-redux';
import { FieldState } from 'react-redux-form';

import { handleErrors, encode } from 'common/utils';
import { CIRSForm, CIRSControl, CIRSErrors } from 'common/forms';
import { CSRFToken } from 'common/components';

interface IAddPhantomFormProps {
    validateSerialUrl: string;
    cancelUrl: string;
    djangoData: {[field: string]: any};
    djangoErrors: {[field: string]: string[]};
    formAction: string;
    phantomState?: { [name: string]: FieldState };
    dispatch?: Dispatch<any>;
}

interface IAddPhantomFormState {
    serialNumberMessage: string | null;
    modelNumber: string | null;
    promise: Bluebird<any> | null;
}

class CreatePhantomFormImpl extends React.Component<IAddPhantomFormProps, IAddPhantomFormState> {
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
        const { cancelUrl, phantomState, formAction, djangoData, djangoErrors } = this.props;
        const {
            serialNumberMessage,
            modelNumber,
        } = this.state;
        const { pristine, validating, valid } = (phantomState as { [name: string]: FieldState }).serial_number;

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
                <CIRSErrors model="phantom" />

                <CIRSForm
                    action={formAction}
                    method="post"
                    model="phantom"
                    className="cirs-form"
                    djangoData={djangoData}
                    djangoErrors={djangoErrors}
                >
                    <CSRFToken />

                    <div>
                        <label>Name</label>
                        <CIRSControl.text model=".name" required />
                        <CIRSErrors model=".name" />
                    </div>

                    {/* TODO doesn't validate on first change */}
                    <div>
                        <label>Serial Number</label>
                        <CIRSControl.text
                            model=".serial_number"
                            asyncValidators={{valid: this.validateSerialNumber.bind(this)}}
                            asyncValidateOn="change"
                            required
                        />
                        <CIRSErrors model=".serial_number" />
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
                </CIRSForm>
            </div>
        );
    }
}

// TODO figure out the types
const CreatePhantomForm = connect<any, any, any>((state: any) => ({phantomState: state.forms.phantom}))
    (CreatePhantomFormImpl as any);
export default CreatePhantomForm;

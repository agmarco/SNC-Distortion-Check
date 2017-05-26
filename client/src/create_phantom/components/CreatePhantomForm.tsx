import React from 'react';
import * as Cookies from 'js-cookie';
import * as Bluebird from 'bluebird';
import { connect } from 'react-redux';
import { Control, Form, Errors, FieldState } from 'react-redux-form';
import uniqueId from 'lodash/uniqueId';
import keyBy from 'lodash/keyBy';

import { handleErrors, encode, fieldErrors } from 'common/utils';
import { CSRFToken } from 'common/components';

interface IAddPhantomFormProps {
    validateSerialUrl: string;
    cancelUrl: string;
    formErrors: {[field: string]: string[]};
    formAction: string;
    phantomState?: { [name: string]: FieldState };
}

interface IAddPhantomFormState {
    serialNumberValid: boolean;
    serialNumberMessage: string | null;
    modelNumber: string | null;
    promise: Bluebird<any> | null;
}

class CreatePhantomFormBase extends React.Component<IAddPhantomFormProps, IAddPhantomFormState> {
    constructor() {
        super();

        Bluebird.config({cancellation: true});
        this.state = {
            serialNumberValid: false,
            serialNumberMessage: null,
            modelNumber: null,
            promise: null,
        };
    }

    validateSerialNumber(value: string, done: Function) {
        console.log("validate");
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
                        serialNumberValid: valid,
                        serialNumberMessage: message,
                        modelNumber: model_number,
                        promise: null,
                    });
                    done(valid);
                }).bind(this));
            });

        this.setState({
            serialNumberValid: false,
            serialNumberMessage: null,
            modelNumber: null,
            promise: newPromise,
        });
    }

    handleSubmit(data: any, event?: Event) {
        // this.form.submit();
    }

    render() {
        const { cancelUrl, formErrors, phantomState, formAction } = this.props;
        const {
            serialNumberValid,
            serialNumberMessage,
            modelNumber,
        } = this.state;
        const { pristine, validating } = (phantomState as { [name: string]: FieldState }).serial_number;

        let modelNumberText = null;
        if (!pristine) {
            if (validating) {
                modelNumberText = "Searching...";
            } else if (serialNumberValid) {
                modelNumberText = <span className="success">{modelNumber}</span>;
            } else {
                modelNumberText = <span className="error">{serialNumberMessage}</span>;
            }
        }

        return (
            <div>
                <Form action={formAction} method="post" model="phantom" className="cirs-form" onSubmit={this.handleSubmit.bind(this)}>
                    <CSRFToken />

                    <Errors
                        model="phantom"
                        messages={formErrors && formErrors.__all__ ? keyBy<string>(formErrors.__all__, uniqueId) : {}}
                    />

                    <div>
                        <label>Name</label>
                        <Control.text model=".name" required />
                        <Errors
                            model=".name"
                            messages={formErrors && formErrors.name ? keyBy<string>(formErrors.name, uniqueId) : {}}
                        />
                    </div>

                    {/* TODO doesn't validate on first change */}
                    <div>
                        <label>Serial Number</label>
                        <Control.text
                            model=".serial_number"
                            required
                            asyncValidators={{
                                invalid: this.validateSerialNumber.bind(this),
                            }}
                            asyncValidateOn="change"
                        />
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
                            disabled={validating || !serialNumberValid}
                            className="btn secondary"
                        />
                    </div>
                </Form>
            </div>
        );
    }
}

// TODO figure out the types
const CreatePhantomForm = connect<any, any, any>((store: any) => ({phantomState: store.forms.phantom}))(CreatePhantomFormBase as any);
export default CreatePhantomForm;

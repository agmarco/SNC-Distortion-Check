import React from 'react';
import * as Cookies from 'js-cookie';
import * as Bluebird from 'bluebird';

import { handleErrors, encode, fieldErrors } from 'common/utils';
import { CSRFToken } from 'common/components';

interface IAddPhantomFormProps {
    validateSerialUrl: string;
    cancelUrl: string;
    formErrors: {[field: string]: string[]};
}

interface IAddPhantomFormState {
    serialNumberPristine: boolean;
    serialNumberFetching: boolean;
    serialNumberValid: boolean;
    serialNumberMessage: string | null;
    modelNumber: string | null;
    promise: Bluebird<any> | null;
}

export default class extends React.Component<IAddPhantomFormProps, IAddPhantomFormState> {
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

        return (
            <div>
                <form method="post" className="cirs-form">
                    <CSRFToken />

                    {fieldErrors(formErrors, '__all__')}

                    <div>
                        <label htmlFor="add-phantom-name">Name</label>
                        <input type="text" id="add-phantom-name" name="name" maxLength={255} required />
                        {fieldErrors(formErrors, 'name')}
                    </div>

                    <div>
                        <label htmlFor="add-phantom-serial">Serial Number</label>
                        <input
                            type="text"
                            id="add-phantom-serial"
                            name="serial_number"
                            maxLength={255}
                            onChange={this.handleSerialChange.bind(this)}
                            required
                        />
                        {fieldErrors(formErrors, 'serial_number')}
                    </div>

                    <div>
                        <label>Model Number</label>
                        <p>{!serialNumberPristine && (serialNumberFetching ? "Searching..." :
                            (serialNumberValid ? <span className="success">{modelNumber}</span> :
                            <span className="error">{serialNumberMessage}</span>))}</p>
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
                            disabled={serialNumberFetching || !serialNumberValid}
                            className="btn secondary"
                        />
                    </div>
                </form>
            </div>
        );
    }
}

import * as React from 'react';
import * as Bluebird from 'bluebird';

import { handleErrors, encode } from 'common/utils';

interface IAddPhantomFormProps {
    createPhantomUrl: string;
    validateSerialUrl: string;
    cancelUrl: string;
    formErrors: {[field: string]: string[]};
    csrftoken: string;
}

interface IAddPhantomFormState {
    validating: boolean;
    valid: boolean;
    modelNumber: string | null;
    promise: Bluebird<any> | null;
}

export default class extends React.Component<IAddPhantomFormProps, IAddPhantomFormState> {
    constructor() {
        super();

        Bluebird.config({cancellation: true});
        this.state = {
            validating: false,
            valid: false,
            modelNumber: null,
            promise: null,
        };
    }

    handleSerialChange(event: React.FormEvent<HTMLInputElement>) {
        const { validateSerialUrl, csrftoken } = this.props;
        const { promise } = this.state;

        if (promise) {
            promise.cancel();
        }

        // validate the serial number
        const newPromise = Bluebird.resolve(fetch(validateSerialUrl, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrftoken,
                },
                body: encode({serial_number: (event.target as any).value}),
            }))
            .then((res) => {
                handleErrors(res, (async function() {
                    const { valid, model_number } = await res.json();

                    this.setState({
                        validating: false,
                        promise: null,
                        valid,
                        model_number,
                    });
                }).bind(this));
            });

        this.setState({validating: true, valid: false, promise: newPromise});
    }

    fieldErrors(field: string) {
        const { formErrors } = this.props;

        return formErrors && formErrors[field] && (
            <ul>
                {formErrors[field].map((error, i) => <li key={i}>{error}</li>)}
            </ul>
        );
    }

    render() {
        const { createPhantomUrl, cancelUrl, csrftoken } = this.props;
        const { validating, valid, modelNumber } = this.state;

        return (
            <div>
                <h1>Add Phantom</h1>
                <form action={createPhantomUrl} method="post">
                    <input type="hidden" name="csrfmiddlewaretoken" value={csrftoken} />

                    <div>
                        {this.fieldErrors('name')}
                        <label htmlFor="add-phantom-name">Name</label>
                        <input type="text" id="add-phantom-name" name="name" maxLength={255} required />
                    </div>

                    <div>
                        {this.fieldErrors('serial_number')}
                        <label htmlFor="add-phantom-serial">Serial Number</label>
                        <input
                            type="text"
                            id="add-phantom-serial"
                            name="serial_number"
                            maxLength={255}
                            onChange={this.handleSerialChange.bind(this)}
                            required
                        />
                    </div>

                    <div>
                        <label>Model Number</label>
                        {valid ? modelNumber : (validating ? "Searching..." : "Invalid Serial Number")}
                    </div>

                    <div>
                        <label>Gold Standard Grid Intersection Locations</label>
                        By default, the new phantom will use gold standard grid intersection locations based on the CAD
                        design for the particular phantom model you select. These points can be customized at any point
                        using a gold standard CT, or a raw point upload.
                    </div>

                    <a href={cancelUrl}>Cancel</a>
                    <input type="submit" value="Add Phantom" disabled={validating || !valid} />
                </form>
            </div>
        );
    }
}

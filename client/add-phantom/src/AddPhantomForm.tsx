import * as React from 'react';
import * as Bluebird from 'bluebird';

import { handleErrors, encode } from 'cirs-common';

interface AddPhantomFormProps {
    create_phantom_url: string;
    validate_serial_url: string;
    cancel_url: string;
    form_errors: {[field: string]: string[]};
    csrftoken: string;
}

interface AddPhantomFormState {
    validating: boolean;
    valid: boolean;
    model_number: string;
    promise: Bluebird<any>;
}

export default class extends React.Component<AddPhantomFormProps, AddPhantomFormState> {
    constructor() {
        super();

        Bluebird.config({cancellation: true});
        this.state = {
            validating: false,
            valid: false,
            model_number: null,
            promise: null,
        };
    }

    handleSerialChange(event: React.FormEvent<HTMLInputElement>) {
        const { validate_serial_url, csrftoken } = this.props;
        const { promise } = this.state;

        if (promise) {
            promise.cancel();
        }

        // validate the serial number
        const newPromise = Bluebird.resolve(fetch(validate_serial_url, {
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
                    })
                }).bind(this));
            });

        this.setState({validating: true, valid: false, promise: newPromise});
    }

    fieldErrors(field: string) {
        const { form_errors } = this.props;

        return form_errors && form_errors[field] && (
            <ul>
                {form_errors[field].map((error) => <li>{error}</li>)}
            </ul>
        );
    }

    render() {
        const { create_phantom_url, cancel_url, csrftoken } = this.props;
        const { validating, valid, model_number } = this.state;

        return (
            <div>
                <h1>Add Phantom</h1>
                <form action={create_phantom_url} method="post">
                    <input type="hidden" name="csrfmiddlewaretoken" value={csrftoken} />

                    <div>
                        {this.fieldErrors('name')}
                        <label htmlFor="add-phantom-name">Name</label>
                        <input type="text" id="add-phantom-name" name="name" maxLength={255} />
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
                        />
                    </div>

                    <div>
                        <label>Model Number</label>
                        {valid ? model_number : (validating ? "Searching..." : "Invalid Serial Number")}
                    </div>

                    <div>
                        <label>Gold Standard Grid Intersection Locations</label>
                        By default, the new phantom will use gold standard grid intersection locations based on the CAD design for the particular phantom model you select. These points can be customized at any point using a gold standard CT, or a raw point upload.
                    </div>

                    <a href={cancel_url}>Cancel</a>
                    <input type="submit" value="Add Phantom" disabled={validating || !valid} />
                </form>
            </div>
        );
    }
}

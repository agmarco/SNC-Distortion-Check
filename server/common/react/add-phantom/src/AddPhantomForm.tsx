import * as React from 'react';
import * as Bluebird from 'bluebird';
import * as Cookies from 'js-cookie';

import { handleErrors } from 'cirs-common';

interface AddPhantomFormProps {
    create_phantom_url: string;
    validate_serial_url: string;
    cancel_url: string;
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
            validating: true,
            valid: false,
            model_number: null,
            promise: null,
        };
    }

    handleSerialChange(event: React.FormEvent<HTMLInputElement>) {
        const { validate_serial_url } = this.props;
        const { promise } = this.state;

        if (promise) {
            promise.cancel();
        }

        const newPromise = Bluebird.resolve(fetch(validate_serial_url, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'X-CSRFToken': Cookies.get('csrftoken'),
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({serial_number: (event.target as any).value}),
            }))
            .then((res) => {
                handleErrors(res, (async function() {
                    const { valid, model_number } = await res.json();

                    this.setState({
                        validating: false,
                        valid,
                        model_number,
                        promise: null,
                    })
                }).bind(this));
            });

        this.setState({validating: true, promise: newPromise});
    }

    render() {
        const { create_phantom_url, cancel_url } = this.props;
        const { validating, valid, model_number } = this.state;

        return (
            <div>
                <h1>Add Phantom</h1>
                <form action={create_phantom_url} method="post">
                    <label htmlFor="add-phantom-name">Name</label>
                    <input type="text" id="add-phantom-name" />
                    <label htmlFor="add-phantom-serial">Serial Number</label>
                    <input type="text" id="add-phantom-serial" onChange={this.handleSerialChange.bind(this)} />
                    <label>Model Number</label>
                    {model_number}
                    <label>Gold Standard Grid Intersection Locations</label>
                    By default, the new phantom will use gold standard grid intersection locations based on the CAD design for the particular phantom model you select. These points can be customized at any point using a gold standard CT, or a raw point upload.
                    <a href={cancel_url}>Cancel</a>
                    <input type="submit" value="Add Phantom" disabled={validating || !valid} />
                </form>
            </div>
        );
    }
}

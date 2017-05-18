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
    fetching: boolean;
    valid: boolean;
    modelNumber: string | null;
    promise: Bluebird<any> | null;
}

export default class extends React.Component<IAddPhantomFormProps, IAddPhantomFormState> {
    constructor() {
        super();

        Bluebird.config({cancellation: true});
        this.state = {
            fetching: false,
            valid: false,
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
                    const { valid, model_number } = await res.json();

                    this.setState({
                        fetching: false,
                        promise: null,
                        modelNumber: model_number,
                        valid,
                    });
                }).bind(this));
            });

        this.setState({fetching: true, valid: false, promise: newPromise});
    }

    render() {
        const { cancelUrl, formErrors } = this.props;
        const { fetching, valid, modelNumber } = this.state;

        return (
            <div>
                <form method="post" className="cirs-form">
                    <CSRFToken />

                    <div>
                        {fieldErrors(formErrors, 'name')}
                        <label htmlFor="add-phantom-name">Name</label>
                        <input type="text" id="add-phantom-name" name="name" maxLength={255} required />
                    </div>

                    <div>
                        {fieldErrors(formErrors, 'serial_number')}
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
                        <p>{valid ? modelNumber : (fetching ? "Searching..." : "Invalid Serial Number")}</p>
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
                            disabled={fetching || !valid}
                            className="btn secondary"
                        />
                    </div>
                </form>
            </div>
        );
    }
}

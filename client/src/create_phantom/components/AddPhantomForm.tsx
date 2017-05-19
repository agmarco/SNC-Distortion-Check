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
    serialNumberFetching: boolean;
    serialNumberAvailable: boolean;
    modelNumber: string | null;
    promise: Bluebird<any> | null;
}

export default class extends React.Component<IAddPhantomFormProps, IAddPhantomFormState> {
    constructor() {
        super();

        Bluebird.config({cancellation: true});
        this.state = {
            serialNumberFetching: false,
            serialNumberAvailable: false,
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
                    const { available, model_number } = await res.json();

                    this.setState({
                        serialNumberFetching: false,
                        serialNumberAvailable: available,
                        modelNumber: model_number,
                        promise: null,
                    });
                }).bind(this));
            });

        this.setState({
            serialNumberFetching: true,
            serialNumberAvailable: false,
            promise: newPromise,
        });
    }

    render() {
        const { cancelUrl, formErrors } = this.props;
        const { serialNumberFetching, serialNumberAvailable, modelNumber } = this.state;

        return (
            <div>
                <form method="post" className="cirs-form">
                    <CSRFToken />

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
                        <p>{serialNumberAvailable ? modelNumber :
                            (serialNumberFetching ? "Searching..." : "Invalid Serial Number")}</p>
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
                            disabled={serialNumberFetching || !serialNumberAvailable}
                            className="btn secondary"
                        />
                    </div>
                </form>
            </div>
        );
    }
}

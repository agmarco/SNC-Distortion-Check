import React from 'react';
import * as Cookies from 'js-cookie';
import * as Bluebird from 'bluebird';

import { handleErrors, encode } from 'common/utils';
import { CSRFToken, BoolIcon } from 'common/components';
import { IMachineSequencePairDTO } from 'common/service';

import './ToleranceForm.scss';

interface IToleranceFormProps {
    updateToleranceUrl: string;
    machineSequencePair: IMachineSequencePairDTO;
    formErrors: {[field: string]: string[]};
    tolerance: number;
    handleToleranceChange: (event: React.FormEvent<HTMLInputElement>) => void;
}

interface IToleranceFormState {
    validating: boolean;
    valid: boolean | null;
    promise: Bluebird<any> | null;
}

export default class extends React.Component<IToleranceFormProps, IToleranceFormState> {
    constructor() {
        super();

        Bluebird.config({cancellation: true});
        this.state = {
            validating: false,
            valid: null,
            promise: null,
        };
    }

    handleSubmit(event: React.FormEvent<HTMLInputElement>) {
        const { updateToleranceUrl, tolerance, machineSequencePair } = this.props;
        const { promise } = this.state;

        event.preventDefault();

        if (promise) {
            promise.cancel();
        }

        const newPromise = Bluebird.resolve(fetch(updateToleranceUrl, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': Cookies.get('csrftoken'),
                },
                body: encode({
                    pk: machineSequencePair.pk,
                    tolerance,
                }),
            }))
            .then((res) => {
                if (res.ok) {
                    this.setState({
                        validating: false,
                        promise: null,
                        valid: true,
                    });
                } else {
                    this.setState({
                        validating: false,
                        promise: null,
                        valid: false,
                    });
                }
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
        const { updateToleranceUrl, tolerance, handleToleranceChange } = this.props;
        const { validating, valid } = this.state;

        return (
            <div>
                <form
                    action={updateToleranceUrl}
                    method="post"
                    className="cirs-form"
                    onSubmit={this.handleSubmit.bind(this)}
                >
                    <CSRFToken />

                    <div>
                        {this.fieldErrors('tolerance')}
                        <label htmlFor="tolerance-tolerance">Maximum FLE (mm)</label>
                        <div className="inline-group">
                            <input
                                type="number"
                                step="0.01"
                                id="tolerance-tolerance"
                                name="tolerance"
                                required
                                value={tolerance}
                                onChange={handleToleranceChange}
                            />
                            <input type="submit" value="Save" className="btn tertiary" />
                            {validating ? <i className="fa fa-spinner fa-pulse fa-3x fa-fw" aria-hidden="true" /> : (
                                valid !== null && <BoolIcon value={valid} />
                            )}
                        </div>
                    </div>
                </form>
            </div>
        );
    }
}

import React from 'react';
import * as Cookies from 'js-cookie';
import * as Bluebird from 'bluebird';

import { encode, fieldErrors } from 'common/utils';
import { CSRFToken, BoolIcon, LoadingIcon } from 'common/components';
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
    fetching: boolean;
    success: boolean | null;
    promise: Bluebird<any> | null;
}

export default class extends React.Component<IToleranceFormProps, IToleranceFormState> {
    constructor() {
        super();

        Bluebird.config({cancellation: true});
        this.state = {
            fetching: false,
            success: null,
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
                        fetching: false,
                        promise: null,
                        success: true,
                    });
                } else {
                    this.setState({
                        fetching: false,
                        promise: null,
                        success: false,
                    });
                }
            });

        this.setState({fetching: true, success: false, promise: newPromise});
    }

    render() {
        const { updateToleranceUrl, tolerance, handleToleranceChange, formErrors } = this.props;
        const { fetching, success } = this.state;

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
                            {fetching ? <LoadingIcon /> : (success !== null && <BoolIcon success={success} />)}
                        </div>
                        {fieldErrors(formErrors, 'tolerance')}
                    </div>
                </form>
            </div>
        );
    }
}

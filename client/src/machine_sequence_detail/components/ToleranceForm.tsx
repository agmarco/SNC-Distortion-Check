import React from 'react';
import * as Cookies from 'js-cookie';
import * as Bluebird from 'bluebird';
import { connect } from 'react-redux';
import { FieldState, actions } from 'react-redux-form';
import { Dispatch } from 'redux';

import { encode } from 'common/utils';
import { CSRFToken, BoolIcon, LoadingIcon } from 'common/components';
import { CirsForm, CirsControl } from 'common/forms';
import { IMachineSequencePairDto } from 'common/service';

import './ToleranceForm.scss';

interface IToleranceFormProps {
    updateToleranceUrl: string;
    machineSequencePair: IMachineSequencePairDto;
    tolerance: number;
    handleToleranceChange: (event: React.FormEvent<HTMLInputElement>) => void;
    formState?: { [name: string]: FieldState };
    dispatch?: Dispatch<any>;
}

interface IToleranceFormState {
    success: boolean | null;
    promise: Bluebird<any> | null;
}

class ToleranceForm extends React.Component<IToleranceFormProps, IToleranceFormState> {
    constructor() {
        super();

        Bluebird.config({cancellation: true});
        this.state = {
            success: null,
            promise: null,
        };
    }

    handleSubmit(data: any, event: React.FormEvent<HTMLInputElement>) {
        const { updateToleranceUrl, tolerance, machineSequencePair, dispatch } = this.props;
        const { promise } = this.state;

        if (promise) {
            promise.cancel();
        }

        if (dispatch) {
            dispatch(actions.setPending('forms.tolerance', true));
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
                if (dispatch) {
                    dispatch(actions.setPending('forms.tolerance', false));
                }
                if (res.ok) {
                    this.setState({
                        promise: null,
                        success: true,
                    });
                } else {
                    this.setState({
                        promise: null,
                        success: false,
                    });
                }
            });

        this.setState({success: false, promise: newPromise});
    }

    render() {
        const { tolerance, handleToleranceChange, formState } = this.props;
        const { success } = this.state;

        const { pending } = (formState as { [name: string]: FieldState }).$form;

        // TODO tolerance form not populating with initial data
        return (
            <div>
                <CirsForm
                    className="cirs-form"
                    id="tolerance-form"
                    model="forms.tolerance"
                    onSubmit={this.handleSubmit.bind(this)}
                    djangoData={{tolerance}}
                >
                    <CSRFToken />

                    <div>
                        <label htmlFor="tolerance-tolerance">Maximum Allowed Distortion Magnitude (mm)</label>
                        <div className="inline-group">
                            <CirsControl.input
                                id="tolerance-tolerance"
                                model=".tolerance"
                                type="number"
                                step="0.01"
                                onChange={handleToleranceChange}
                                required
                            />
                            <input type="submit" value="Save" className="btn tertiary" />
                            {pending ? <LoadingIcon /> : (success !== null && <BoolIcon success={success} />)}
                        </div>
                    </div>
                </CirsForm>
            </div>
        );
    }
}

export default connect<any, any, any>((state: any) => ({formState: state.forms.forms.tolerance}))(ToleranceForm as any);

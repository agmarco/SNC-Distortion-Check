import React from 'react';
import { connect } from 'react-redux';
import { FieldState } from 'react-redux-form';
import { Dispatch } from 'redux';

import { CSRFToken, BoolIcon, LoadingIcon } from 'common/components';
import { CirsForm, CirsControl } from 'common/forms';
import { IMachineSequencePairDto } from 'common/service';
import { IAppState } from '../reducers';
import * as actions from '../actions';

import './ToleranceForm.scss';


interface IToleranceFormProps {
    machineSequencePair: IMachineSequencePairDto;
    tolerance: number;
    handleToleranceChange: (event: React.FormEvent<HTMLInputElement>) => void;
    formState?: { [name: string]: FieldState };
    dispatch?: Dispatch<any>;
    updateToleranceSuccess?: boolean | null;
}


class ToleranceForm extends React.Component<IToleranceFormProps, {}> {
    handleSubmit(data: any, event: React.FormEvent<HTMLInputElement>) {
        const { tolerance, machineSequencePair, dispatch } = this.props;

        if (dispatch) {
            dispatch(actions.updateTolerance({pk: machineSequencePair.pk, tolerance}));
        }
    }

    render() {
        const { handleToleranceChange, formState, updateToleranceSuccess } = this.props;

        const { pending } = (formState as { [name: string]: FieldState }).$form;

        return (
            <div>
                <CirsForm
                    className="cirs-form"
                    id="tolerance-form"
                    model="forms.tolerance"
                    onSubmit={this.handleSubmit.bind(this)}
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
                            {pending ? <LoadingIcon /> :
                                (updateToleranceSuccess !== null &&
                                <BoolIcon success={updateToleranceSuccess as boolean} />)}
                        </div>
                    </div>
                </CirsForm>
            </div>
        );
    }
}
export default connect<any, any, any>((state: IAppState) => ({
    formState: state.forms.forms.tolerance,
    updateToleranceSuccess: state.updateToleranceSuccess,
}))(ToleranceForm as any);

import React from 'react';
import { Dispatch } from 'redux';
import { connect } from 'react-redux';
import { FieldState } from 'react-redux-form';

import { CirsForm, CirsControl, CirsErrors, IDjangoFormErrors } from 'common/forms';
import { CSRFToken } from 'common/components';
import { ICreatePhantomForm } from '../forms';
import { IAppState, ISerialNumberInfoState } from '../reducers';
import * as actions from '../actions';

interface ICreatePhantomFormProps {
    cancelUrl: string;
    formErrors: IDjangoFormErrors | null;
    formAction: string;
    form?: ICreatePhantomForm;
    formState?: { [name: string]: FieldState };
    dispatch?: Dispatch<any>;
    serialNumberInfo?: ISerialNumberInfoState;
}

class CreatePhantomForm extends React.Component<ICreatePhantomFormProps, {}> {
    componentDidMount() {
        const { form } = this.props;

        if (form) {
            this.validateSerialNumber({target: {value: form.serial_number}});
        }
    }

    validateSerialNumber(event: any) {
        const { dispatch } = this.props;

        if (dispatch) {
            dispatch(actions.validateSerialNumber((event.target as any).value));
        }
    }

    render() {
        const { cancelUrl, formState, formAction, formErrors, serialNumberInfo } = this.props;
        const { message, modelNumber} = serialNumberInfo as ISerialNumberInfoState;
        const { pristine, validating, valid } = (formState as { [name: string]: FieldState }).serial_number;

        let modelNumberText = null;
        if (!pristine) {
            if (validating) {
                modelNumberText = "Searching...";
            } else if (valid) {
                modelNumberText = <span className="success">{modelNumber}</span>;
            } else {
                modelNumberText = <span className="error">{message}</span>;
            }
        }

        return (
            <div>
                <CirsForm
                    action={formAction}
                    method="post"
                    model="forms.phantom"
                    className="cirs-form"
                    djangoErrors={formErrors}
                >
                    <CirsControl type="hidden" model=".__all__" />
                    <CirsErrors model=".__all__" />

                    <CSRFToken />

                    <div>
                        <label htmlFor="phantom-name">Name</label>
                        <CirsControl.text id="phantom-name" model=".name" required />
                        <CirsErrors model=".name" required />
                    </div>

                    <div>
                        <label htmlFor="phantom-serial-number">Serial Number</label>
                        <CirsControl.text
                            id="phantom-serial-number"
                            model=".serial_number"
                            onChange={this.validateSerialNumber.bind(this)}
                            required
                        />
                        {/*<CirsErrors model=".serial_number" required />*/}
                    </div>

                    <div>
                        <label>Model Number</label>
                        <p>{modelNumberText}</p>
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
                            disabled={validating || !valid}
                            className="btn secondary"
                        />
                    </div>
                </CirsForm>
            </div>
        );
    }
}

// TODO figure out the types
export default connect<any, any, any>((state: IAppState) => ({
    form: state.forms.phantom,
    formState: state.forms.forms.phantom,
    serialNumberInfo: state.serialNumberInfo,
}))(CreatePhantomForm as any);

import React from 'react';
import { Dispatch } from 'redux';
import { FieldState } from 'react-redux-form';

import { CirsForm, CirsControl, CirsErrors, IDjangoFormData, IDjangoFormErrors } from 'common/forms';
import { CSRFToken } from 'common/components';


interface IUpdatePhantomFormProps {
    formErrors: IDjangoFormErrors | null;
    formAction: string;
    formState?: { [name: string]: FieldState };
    dispatch?: Dispatch<any>;
}


export default class extends React.Component<IUpdatePhantomFormProps, {}> {
    render() {
        const { formAction, formErrors } = this.props;

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
                        <div className="inline-group">
                            <CirsControl.text id="phantom-name" model=".name" required />
                            <input
                                type="submit"
                                value="Save Name Change"
                                className="btn tertiary"
                            />
                        </div>
                        <CirsErrors model=".name" required />
                    </div>
                </CirsForm>
            </div>
        );
    }
}

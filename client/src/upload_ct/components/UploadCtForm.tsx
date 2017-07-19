import React from 'react';
import { connect } from 'react-redux';
import { FieldState } from 'react-redux-form';
import { Dispatch } from 'redux';

import { CSRFToken, LoadingIcon } from 'common/components';
import { CirsForm, CirsControl, CirsErrors, IDjangoFormErrors } from 'common/forms';
import { IUploadCtForm } from '../forms';
import * as actions from '../actions';

interface IUploadCtFormProps {
    cancelUrl: string;
    formErrors: IDjangoFormErrors | null;
    formAction: string;
    form?: IUploadCtForm;
    formState?: { [name: string]: FieldState };
    dispatch?: Dispatch<any>;
}

class UploadCtForm extends React.Component<IUploadCtFormProps, {}> {
    formId = 'upload-ct';

    handleSubmit(data: IUploadCtForm, event: React.FormEvent<HTMLInputElement>) {
        const { dispatch, formState } = this.props;

        if (!(formState && formState.$form && formState.$form.submitted)) {
            event.preventDefault();
            if (dispatch) {
                dispatch(actions.uploadCtToS3({
                    file: data.dicom_archive[0],
                    formId: this.formId,
                }));
            }
        }
    }

    render() {
        const { cancelUrl, formErrors, formState, formAction } = this.props;


        return (
            <div>
                <CirsForm
                    action={formAction}
                    method="post"
                    model="uploadCt"
                    className="cirs-form"
                    djangoErrors={formErrors}
                    onSubmit={this.handleSubmit.bind(this)}
                    id={this.formId}
                >

                    <CirsControl type="hidden" model=".__all__" />
                    <CirsErrors model=".__all__" />

                    <CSRFToken />

                    <CirsControl type="hidden" model=".dicom_archive_url" />

                    <div>
                        <label htmlFor="upload-ct-dicom-archive">File Browser</label>
                        <CirsControl.file type="file" id="upload-ct-dicom-archive" model=".dicom_archive" required />
                        <CirsErrors model=".dicom_archive" required />
                        <p>
                            The uploaded file should be a zip-archive containing CT DICOM slices for the gold standard
                            CT scan of the phantom.
                        </p>
                    </div>

                    <div className="form-links">
                        <a href={cancelUrl} className="btn tertiary">Cancel</a>
                        <input type="submit" value="Upload CT" className="btn secondary" />
                    </div>

                    {formState && formState.$form && formState.$form.pending &&
                    <p>Your file is uploading... <LoadingIcon /></p>}
                </CirsForm>
            </div>
        );
    }
}

export default connect<any, any, any>((state: any) => ({
    form: state.uploadCt,
    formState: state.forms.uploadCt,
}))(UploadCtForm as any);

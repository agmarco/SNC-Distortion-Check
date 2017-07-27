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

interface IUploadCtFormState {
    dicomArchiveDisabled: boolean;
}

class UploadCtForm extends React.Component<IUploadCtFormProps, IUploadCtFormState> {
    constructor() {
        super();
        this.state = {dicomArchiveDisabled: false};
    }

    handleSubmit() {
        this.setState({dicomArchiveDisabled: true});
    }

    handleDicomArchiveChange(event: React.FormEvent<HTMLInputElement>) {
        const { dispatch } = this.props;
        const value = (event.target as any).files;

        if (value) {
            if (dispatch) {
                dispatch(actions.uploadCtToS3(value[0]));
            }
        }
    }

    render() {
        const { cancelUrl, formErrors, formState, formAction } = this.props;
        const { dicomArchiveDisabled } = this.state;
        const dicomArchiveState: FieldState | undefined = formState && formState.dicom_archive &&
            (formState.dicom_archive as FieldState[])[0];


        return (
            <div>
                <CirsForm
                    action={formAction}
                    method="post"
                    model="uploadCt"
                    className="cirs-form"
                    djangoErrors={formErrors}
                    onSubmit={this.handleSubmit.bind(this)}
                >

                    <CirsControl type="hidden" model=".__all__" />
                    <CirsErrors model=".__all__" />

                    <CSRFToken />

                    <CirsControl type="hidden" model=".dicom_archive_url" />

                    <div>
                        <label htmlFor="upload-ct-dicom-archive">File Browser</label>
                        <CirsControl.file type="file" id="upload-ct-dicom-archive" model=".dicom_archive" required
                                          onChange={this.handleDicomArchiveChange.bind(this)}
                                          disabled={dicomArchiveDisabled}/>
                        <p>
                            The uploaded file should be a zip-archive containing CT DICOM slices for the gold standard
                            CT scan of the phantom.
                        </p>

                        <CirsErrors model=".dicom_archive" required />

                        {dicomArchiveState && dicomArchiveState.pending &&
                        <p>Please wait while your file uploads... <LoadingIcon /></p>}

                        {dicomArchiveState && !dicomArchiveState.pristine && !dicomArchiveState.pending &&
                        dicomArchiveState.valid && <p className="success">Your file has been uploaded successfully.</p>}
                    </div>

                    <div className="form-links">
                        <a href={cancelUrl} className="btn tertiary">Cancel</a>
                        <input type="submit" value="Upload CT" className="btn secondary"
                               disabled={dicomArchiveState && dicomArchiveState.pending}/>
                    </div>
                </CirsForm>
            </div>
        );
    }
}

export default connect<any, any, any>((state: any) => ({
    form: state.uploadCt,
    formState: state.forms.uploadCt,
}))(UploadCtForm as any);

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
    submitted: boolean;
}

class UploadCtForm extends React.Component<IUploadCtFormProps, IUploadCtFormState> {
    submit: HTMLInputElement;

    constructor() {
        super();
        this.state = {submitted: false};
    }

    componentDidUpdate() {
        // Once the file is uploaded to S3, the formState is updated by the uploadToS3 saga
        const { formState } = this.props;
        const dicomArchiveState: FieldState | undefined = formState && formState.dicom_archive &&
            (formState.dicom_archive as FieldState[])[0];
        if (dicomArchiveState && !dicomArchiveState.pristine && !dicomArchiveState.pending &&
            dicomArchiveState.valid && !this.state.submitted) {
            this.submit.click();
            this.setState({submitted: true});
        }
    }

    handleDicomArchiveChange(event: React.FormEvent<HTMLInputElement>) {
        const { dispatch } = this.props;
        const value = (event.target as any).files;

        if (value) {
            dispatch!(actions.uploadCtToS3(value[0]));
        }
    }

    render() {
        const { cancelUrl, formErrors, formState, formAction } = this.props;
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
                >

                    <CirsControl type="hidden" model=".__all__" />
                    <CirsErrors model=".__all__" />

                    <CSRFToken />

                    <CirsControl type="hidden" model=".dicom_archive_url" />

                    <div>
                        <label htmlFor="upload-ct-dicom-archive">File Browser</label>
                        {/* TODO: accept=".zip" breaks the input */}
                        <CirsControl.file type="file" id="upload-ct-dicom-archive" model=".dicom_archive"
                                          required
                                          onChange={this.handleDicomArchiveChange.bind(this)} />
                        <p>
                            The uploaded file should be a zip-archive containing CT DICOM slices for the gold standard
                            CT scan of the phantom.
                        </p>

                        <CirsErrors model=".dicom_archive" required />

                        {dicomArchiveState && dicomArchiveState.pending &&
                        <p>Please wait while your file uploads... <LoadingIcon /></p>}
                    </div>

                    <div className="form-links">
                        <a href={cancelUrl} className="btn tertiary">Cancel</a>
                        <input ref={submit => this.submit = submit}
                               type="submit" value="Upload CT" className="btn secondary"
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
}))(UploadCtForm);

import React from 'react';
import { connect } from 'react-redux';
import { actions as formActions, FieldState } from 'react-redux-form';
import { Dispatch } from 'redux';

import { IMachineDto, ISequenceDto, IPhantomDto } from 'common/service';
import { CSRFToken, LoadingIcon } from 'common/components';
import { CirsForm, CirsControl, CirsErrors, IDjangoFormErrors } from 'common/forms';
import { IUploadScanForm } from '../forms';
import * as actions from '../actions';

interface IUploadScanFormProps {
    machines: IMachineDto[];
    sequences: ISequenceDto[];
    phantoms: IPhantomDto[];
    initialMachinePk: number | null;
    initialSequencePk: number | null;
    cancelUrl: string;
    formErrors: IDjangoFormErrors | null;
    formAction: string;
    form?: IUploadScanForm;
    formState?: { [name: string]: FieldState };
    dispatch?: Dispatch<any>;
}

interface IUploadScanFormState {
    dicomArchiveDisabled: boolean;
}

class UploadScanForm extends React.Component<IUploadScanFormProps, IUploadScanFormState> {
    constructor(props: IUploadScanFormProps) {
        super();
        const { initialMachinePk, initialSequencePk, dispatch } = props;

        if (dispatch) {
            dispatch(formActions.change('uploadScan.machine', initialMachinePk || ''));
            dispatch(formActions.change('uploadScan.sequence', initialSequencePk || ''));
            dispatch(formActions.change('uploadScan.phantom', ''));
        }
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
                dispatch(actions.uploadScanToS3(value[0]));
            }
        }
    }

    render() {
        const { machines, sequences, phantoms, cancelUrl, formErrors, form, formState, formAction } = this.props;
        const { dicomArchiveDisabled } = this.state;
        const { machine, sequence, phantom } = form as IUploadScanForm;
        const dicomArchiveState: FieldState | undefined = formState && formState.dicom_archive &&
            (formState.dicom_archive as FieldState[])[0];

        const currentMachine = machine && (
            machines.find((m) => m.pk === Number(machine))
        );
        const currentSequence = sequence && (
            sequences.find((s) => s.pk === Number(sequence))
        );
        const currentPhantom = phantom && (
            phantoms.find((p) => p.pk === Number(phantom))
        );

        return (
            <div>
                <CirsForm
                    action={formAction}
                    method="post"
                    model="uploadScan"
                    encType="multipart/form-data"
                    className="cirs-form"
                    djangoErrors={formErrors}
                    onSubmit={this.handleSubmit.bind(this)}
                >

                    <CirsControl type="hidden" model=".__all__" />
                    <CirsErrors model=".__all__" />

                    <CSRFToken />

                    <CirsControl type="hidden" model=".dicom_archive_url" />

                    <div>
                        <label htmlFor="upload-scan-machine">Machine</label>
                        <CirsControl.select
                            id="upload-scan-machine"
                            model=".machine"
                            required
                        >
                            <option value="" disabled />
                            {machines.map((m) => <option value={m.pk} key={m.pk}>{m.name}</option>)}
                        </CirsControl.select>
                        <CirsErrors model=".machine" required />

                        {currentMachine && (
                            <div>
                                <div>
                                    <label>Model</label>
                                    <p>{currentMachine.model}</p>
                                </div>
                                <div>
                                    <label>Vendor</label>
                                    <p>{currentMachine.manufacturer}</p>
                                </div>
                            </div>
                        )}
                    </div>

                    <div>
                        <label htmlFor="upload-scan-sequence">Sequence</label>
                        <CirsControl.select
                            id="upload-scan-sequence"
                            model=".sequence"
                            required
                        >
                            <option value="" disabled />
                            {sequences.map((s) => <option value={s.pk} key={s.pk}>{s.name}</option>)}
                        </CirsControl.select>
                        <CirsErrors model=".sequence" required />

                        {currentSequence && (
                            <div>
                                <div>
                                    <label>Instructions</label>
                                    <p>{currentSequence.instructions}</p>
                                </div>
                            </div>
                        )}
                    </div>

                    <div>
                        <label htmlFor="upload-scan-phantom">Phantom</label>
                        <CirsControl.select
                            id="upload-scan-phantom"
                            model=".phantom"
                            required
                        >
                            <option value="" disabled />
                            {phantoms.map((p) => <option value={p.pk} key={p.pk}>{p.name}</option>)}
                        </CirsControl.select>
                        <CirsErrors model=".phantom" required />

                        {currentPhantom && (
                            <div>
                                <div>
                                    <label>Model Number</label>
                                    <p>{currentPhantom.model_number}</p>
                                </div>
                                <div>
                                    <label>Serial Number</label>
                                    <p>{currentPhantom.serial_number}</p>
                                </div>
                                <div>
                                    <label>Gold Standard Grid Locations</label>
                                    <p>{currentPhantom.gold_standard_grid_locations}</p>
                                </div>
                            </div>
                        )}
                    </div>

                    <div>
                        <label htmlFor="upload-scan-dicom-archive">MRI Scan Files</label>
                        {/* TODO: accept=".zip" breaks the input */}
                        <CirsControl.file type="file" id="upload-scan-dicom-archive" model=".dicom_archive"
                                          required
                                          onChange={this.handleDicomArchiveChange.bind(this)}
                                          disabled={dicomArchiveDisabled} />
                        <p>
                            Please upload a zip-file containing the MRI DICOM files of a scan of the specified phatom,
                            on the specified machine, using the specified sequence.
                        </p>

                        <CirsErrors model=".dicom_archive.0" required />

                        {dicomArchiveState && dicomArchiveState.pending &&
                        <p>Please wait while your file uploads... <LoadingIcon /></p>}

                        {dicomArchiveState && !dicomArchiveState.pristine && !dicomArchiveState.pending &&
                        dicomArchiveState.valid && <p className="success">Your file has been uploaded successfully.</p>}
                    </div>

                    <div>
                        <label htmlFor="upload-scan-notes">Notes</label>
                        <CirsControl.textarea cols={40} rows={10} id="upload-scan-notes" model=".notes" />
                        <CirsErrors model=".notes" />
                    </div>

                    <div className="form-links">
                        <a href={cancelUrl} className="btn tertiary">Cancel</a>
                        <input type="submit" value="Process Scan" className="btn secondary"
                               disabled={dicomArchiveState && dicomArchiveState.pending} />
                    </div>
                </CirsForm>
            </div>
        );
    }
}

export default connect<any, any, any>((state: any) => ({
    form: state.uploadScan,
    formState: state.forms.uploadScan,
}))(UploadScanForm as any);

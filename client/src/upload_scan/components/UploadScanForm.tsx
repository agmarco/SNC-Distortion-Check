import React from 'react';
import { connect } from 'react-redux';
import { actions as formActions, FormState } from 'react-redux-form';
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
    formState?: FormState;
    dispatch?: Dispatch<any>;
}

class UploadScanForm extends React.Component<IUploadScanFormProps, {}> {
    formId: string;

    constructor(props: IUploadScanFormProps) {
        super();

        const { initialMachinePk, initialSequencePk, dispatch } = props;
        if (dispatch) {
            dispatch(formActions.change('uploadScan.machine', initialMachinePk || ''));
            dispatch(formActions.change('uploadScan.sequence', initialSequencePk || ''));
            dispatch(formActions.change('uploadScan.phantom', ''));
        }
        this.formId = 'upload-scan';
    }

    handleSubmit(data: IUploadScanForm) {
        const { dispatch } = this.props;

        // TODO: data.dicom_archive may not be correct
        // console.log(data.dicom_archive)

        if (dispatch) {
            dispatch(actions.uploadScanToS3({
                file: data.dicom_archive[0],
                formId: this.formId,
            }));
        }
    }

    render() {
        const { machines, sequences, phantoms, cancelUrl, formErrors, form, formState, formAction } = this.props;
        const { machine, sequence, phantom } = form as IUploadScanForm;

        const currentMachine = machine && (
            machines.find((m) => m.pk === Number(machine))
        );
        const currentSequence = sequence && (
            sequences.find((s) => s.pk === Number(sequence))
        );
        const currentPhantom = phantom && (
            phantoms.find((p) => p.pk === Number(phantom))
        );

        // TODO: formState may not be correct
        // console.log(formState)

        return (
            <div>
                <CirsForm
                    action={formAction}
                    encType="multipart/form-data"
                    method="post"
                    model="uploadScan"
                    className="cirs-form"
                    djangoErrors={formErrors}
                    onSubmit={this.handleSubmit.bind(this)}
                    id={this.formId}
                >

                    <CirsControl type="hidden" model=".__all__" />
                    <CirsErrors model=".__all__" />

                    {formState && formState.pending && <p>Your file is uploading... <LoadingIcon /></p>}

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
                        <CirsControl.file type="file" id="upload-scan-dicom-archive" model=".dicom_archive" required />
                        <CirsErrors model=".dicom_archive" required />
                        <p>
                            Please upload a zip-file containing the MRI DICOM files of a scan of the specified phatom,
                            on the specified machine, using the specified sequence.
                        </p>
                    </div>

                    <div>
                        <label htmlFor="upload-scan-notes">Notes</label>
                        <CirsControl.textarea cols={40} rows={10} id="upload-scan-notes" model=".notes" />
                        <CirsErrors model=".notes" />
                    </div>

                    <div className="form-links">
                        <a href={cancelUrl} className="btn tertiary">Cancel</a>
                        <input type="submit" value="Process Scan" className="btn secondary" />
                    </div>
                </CirsForm>
            </div>
        );
    }
}

// TODO: fix upload issue and remove the warning
// message; also remove the same message from the
// static Heroku error page in S3.
export default connect<any, any, any>((state: any) => ({
    form: state.uploadScan,
    formState: state.forms.uploadScan,
}))(UploadScanForm as any);

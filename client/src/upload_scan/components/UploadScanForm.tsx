import React from 'react';

import { IMachineDTO, ISequenceDTO, IPhantomDTO } from 'common/service';
import { CSRFToken } from 'common/components';
import { fieldErrors } from 'common/utils';

interface IUploadScanFormProps {
    machines: IMachineDTO[];
    sequences: ISequenceDTO[];
    phantoms: IPhantomDTO[];
    uploadScanUrl: string;
    cancelUrl: string;
    formErrors: {[field: string]: string[]};
}

interface IUploadScanFormState {
    machineFilterValue: '' | number;
    sequenceFilterValue: '' | number;
    phantomFilterValue: '' | number;
}

export default class extends React.Component<IUploadScanFormProps, IUploadScanFormState> {
    constructor() {
        super();

        this.state = {
            machineFilterValue: '',
            sequenceFilterValue: '',
            phantomFilterValue: '',
        };
    }

    handleMachineChange(event: React.FormEvent<HTMLInputElement>) {
        const value = (event.target as any).value;
        this.setState({machineFilterValue: value === '' ? value : Number(value)});
    }

    handleSequenceChange(event: React.FormEvent<HTMLInputElement>) {
        const value = (event.target as any).value;
        this.setState({sequenceFilterValue: value === '' ? value : Number(value)});
    }

    handlePhantomChange(event: React.FormEvent<HTMLInputElement>) {
        const value = (event.target as any).value;
        this.setState({phantomFilterValue: value === '' ? value : Number(value)});
    }

    render() {
        const { machines, sequences, phantoms, uploadScanUrl, cancelUrl, formErrors } = this.props;
        const { machineFilterValue, sequenceFilterValue, phantomFilterValue } = this.state;

        const currentMachine = machineFilterValue && (
            machines.find((m) => m.pk === machineFilterValue)
        );
        const currentSequence = sequenceFilterValue && (
            sequences.find((s) => s.pk === sequenceFilterValue)
        );
        const currentPhantom = phantomFilterValue && (
            phantoms.find((p) => p.pk === phantomFilterValue)
        );

        return (
            <div>
                <form action={uploadScanUrl} encType="multipart/form-data" method="post" className="cirs-form">
                    <CSRFToken />

                    <div>
                        {fieldErrors(formErrors, 'machine')}

                        <label htmlFor="upload-scan-machine">Machine</label>
                        <select
                            id="upload-scan-machine"
                            name="machine"
                            value={machineFilterValue}
                            onChange={this.handleMachineChange.bind(this)}
                            required
                        >
                            <option value="" disabled />
                            {machines.map((m) => <option value={m.pk} key={m.pk}>{m.name}</option>)}
                        </select>

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
                        {fieldErrors(formErrors, 'sequence')}

                        <label htmlFor="upload-scan-sequence">Sequence</label>
                        <select
                            id="upload-scan-sequence"
                            name="sequence"
                            value={sequenceFilterValue}
                            onChange={this.handleSequenceChange.bind(this)}
                            required
                        >
                            <option value="" disabled />
                            {sequences.map((s) => <option value={s.pk} key={s.pk}>{s.name}</option>)}
                        </select>

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
                        {fieldErrors(formErrors, 'phantom')}

                        <label htmlFor="upload-scan-phantom">Phantom</label>
                        <select
                            id="upload-scan-phantom"
                            name="phantom"
                            value={phantomFilterValue}
                            onChange={this.handlePhantomChange.bind(this)}
                            required
                        >
                            <option value="" disabled />
                            {phantoms.map((p) => <option value={p.pk} key={p.pk}>{p.name}</option>)}
                        </select>

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
                        {fieldErrors(formErrors, 'dicom_archive')}

                        <label htmlFor="upload-scan-dicom-archive">MRI Scan Files</label>
                        <input id="upload-scan-dicom-archive" name="dicom_archive" type="file" required />
                        <p>
                            Please upload a zip-file containing the MRI DICOM files of a scan of the specified phatom,
                            on the specified machine, using the specified sequence.
                        </p>
                    </div>

                    <div>
                        {fieldErrors(formErrors, 'notes')}

                        <label htmlFor="upload-scan-notes">Notes</label>
                        <textarea cols={40} rows={10} id="upload-scan-notes" name="notes" />
                    </div>

                    <div className="form-links">
                        <a href={cancelUrl} className="btn tertiary">Cancel</a>
                        <input type="submit" value="Process Scan" className="btn secondary" />
                    </div>
                </form>
            </div>
        );
    }
}

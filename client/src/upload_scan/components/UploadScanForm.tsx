import * as React from 'react';

import { IMachineDTO, ISequenceDTO, IPhantomDTO } from 'common/service';
import { CSRFToken } from 'common/components';

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

    fieldErrors(field: string) {
        const { formErrors } = this.props;

        return formErrors && formErrors[field] && (
            <ul>
                {formErrors[field].map((error, i) => <li key={i}>{error}</li>)}
            </ul>
        );
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
        const { machines, sequences, phantoms, uploadScanUrl, cancelUrl } = this.props;
        const { machineFilterValue, sequenceFilterValue, phantomFilterValue } = this.state;

        const currentMachine = machineFilterValue && (
            machines.find((machine) => machine.pk === machineFilterValue)
        );
        const currentSequence = sequenceFilterValue && (
            sequences.find((sequence) => sequence.pk === sequenceFilterValue)
        );
        const currentPhantom = phantomFilterValue && (
            phantoms.find((phantom) => phantom.pk === phantomFilterValue)
        );

        return (
            <div>
                <form action={uploadScanUrl} encType="multipart/form-data" method="post" className="cirs-form">
                    <CSRFToken />

                    <div>
                        {this.fieldErrors('machine')}

                        <label htmlFor="upload-scan-machine">Machine</label>
                        <select
                            id="upload-scan-machine"
                            name="machine"
                            value={machineFilterValue}
                            onChange={this.handleMachineChange.bind(this)}
                            required
                        >
                            <option value="" disabled />
                            {machines.map((machine) => (
                                <option value={machine.pk} key={machine.pk}>{machine.name}</option>
                            ))}
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
                        {this.fieldErrors('sequence')}

                        <label htmlFor="upload-scan-sequence">Sequence</label>
                        <select
                            id="upload-scan-sequence"
                            name="sequence"
                            value={sequenceFilterValue}
                            onChange={this.handleSequenceChange.bind(this)}
                            required
                        >
                            <option value="" disabled />
                            {sequences.map((sequence) => (
                                <option value={sequence.pk} key={sequence.pk}>{sequence.name}</option>
                            ))}
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
                        {this.fieldErrors('phantom')}

                        <label htmlFor="upload-scan-phantom">Phantom</label>
                        <select
                            id="upload-scan-phantom"
                            name="phantom"
                            value={phantomFilterValue}
                            onChange={this.handlePhantomChange.bind(this)}
                            required
                        >
                            <option value="" disabled />
                            {phantoms.map((phantom) => (
                                <option value={phantom.pk} key={phantom.pk}>{phantom.name}</option>
                            ))}
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
                        {this.fieldErrors('dicom_archive')}

                        <label htmlFor="upload-scan-dicom-archive">MRI Scan Files</label>
                        <input id="upload-scan-dicom-archive" name="dicom_archive" type="file" required />
                        <p>
                            Please upload a zip-file containing the MRI DICOM files of a scan of the specified phatom,
                            on the specified machine, using the specified sequence.
                        </p>
                    </div>

                    <div>
                        {this.fieldErrors('notes')}

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

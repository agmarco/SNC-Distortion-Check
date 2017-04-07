import * as React from 'react';

import { IMachineDTO, ISequenceDTO, IPhantomDTO } from 'common/service';

interface IUploadScanFormProps {
    machines: IMachineDTO[];
    sequences: ISequenceDTO[];
    phantoms: IPhantomDTO[];
    uploadScanUrl: string;
    cancelUrl: string;
    formErrors: {[field: string]: string[]};
    csrftoken: string;
}

interface IUploadScanFormState {
    machineFilterValue: string|number;
    sequenceFilterValue: string|number;
    phantomFilterValue: string|number;
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
        this.setState({machineFilterValue: Number((event.target as any).value)});
    }

    handleSequenceChange(event: React.FormEvent<HTMLInputElement>) {
        this.setState({sequenceFilterValue: Number((event.target as any).value)});
    }

    handlePhantomChange(event: React.FormEvent<HTMLInputElement>) {
        this.setState({phantomFilterValue: Number((event.target as any).value)});
    }

    render() {
        const { machines, sequences, phantoms, uploadScanUrl, cancelUrl, csrftoken } = this.props;
        const { machineFilterValue, sequenceFilterValue, phantomFilterValue } = this.state;

        const currentMachine = machineFilterValue && machines.find((machine) => machine.pk === machineFilterValue);
        const currentSequence = sequenceFilterValue && sequences.find((sequence) => {
            return sequence.pk === sequenceFilterValue;
        });
        const currentPhantom = phantomFilterValue && phantoms.find((phantom) => phantom.pk === phantomFilterValue);

        return (
            <div>
                <h1>Upload Scan</h1>
                <form action={uploadScanUrl} encType="multipart/form-data" method="post">
                    <input type="hidden" name="csrfmiddlewaretoken" value={csrftoken} />

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
                                    {currentMachine.model}
                                </div>
                                <div>
                                    <label>Vendor</label>
                                    {currentMachine.manufacturer}
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
                                    {currentSequence.instructions}
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
                                    {currentPhantom.model_number}
                                </div>
                                <div>
                                    <label>Serial Number</label>
                                    {currentPhantom.serial_number}
                                </div>
                                <div>
                                    <label>Gold Standard Grid Locations</label>
                                    {currentPhantom.gold_standard_grid_locations}
                                </div>
                            </div>
                        )}
                    </div>

                    <div>
                        {this.fieldErrors('dicom_archive')}

                        <label htmlFor="upload-scan-dicom-archive">MRI Scan Files</label>
                        <input id="upload-scan-dicom-archive" name="dicom_archive" type="file" required />
                        Please upload a zip-file containing the MRI DICOM files of a scan of the specified phatom, on
                        the specified machine, using the specified sequence.
                    </div>

                    <div>
                        {this.fieldErrors('notes')}

                        <label htmlFor="upload-scan-notes">Notes</label>
                        <textarea cols={40} rows={10} id="upload-scan-notes" name="notes" />
                    </div>

                    <a href={cancelUrl}>Cancel</a>
                    <input type="submit" value="Process Scan" />
                </form>
            </div>
        );
    }
}

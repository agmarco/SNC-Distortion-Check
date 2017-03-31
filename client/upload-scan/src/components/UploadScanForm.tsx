import * as React from 'react';

import { MachineDTO, SequenceDTO, PhantomDTO} from 'common/service';

interface UploadScanFormProps {
    machines: MachineDTO[];
    sequences: SequenceDTO[];
    phantoms: PhantomDTO[];
    upload_scan_url: string;
    cancel_url: string;
    form_errors: {[field: string]: string[]};
    csrftoken: string;
}

interface UploadScanFormState {
    currentMachinePk: string|number;
    currentSequencePk: string|number;
    currentPhantomPk: string|number;
}

export default class extends React.Component<UploadScanFormProps, UploadScanFormState> {
    constructor() {
        super();

        this.state = {
            currentMachinePk: '',
            currentSequencePk: '',
            currentPhantomPk: '',
        };
    }
    fieldErrors(field: string) {
        const { form_errors } = this.props;

        return form_errors && form_errors[field] && (
            <ul>
                {form_errors[field].map((error) => <li>{error}</li>)}
            </ul>
        );
    }

    handleMachineChange(event: React.FormEvent<HTMLInputElement>) {
        this.setState({currentMachinePk: Number((event.target as any).value)})
    }

    handleSequenceChange(event: React.FormEvent<HTMLInputElement>) {
        this.setState({currentSequencePk: Number((event.target as any).value)})
    }

    handlePhantomChange(event: React.FormEvent<HTMLInputElement>) {
        this.setState({currentPhantomPk: Number((event.target as any).value)})
    }

    render() {
        const { machines, sequences, phantoms, upload_scan_url, cancel_url, csrftoken } = this.props;
        const { currentMachinePk, currentSequencePk, currentPhantomPk } = this.state;

        const currentMachine = currentMachinePk ? machines.find((machine) => machine.pk === currentMachinePk) : null;
        const currentSequence = currentSequencePk ? sequences.find((sequence) => sequence.pk === currentSequencePk) : null;
        const currentPhantom = currentPhantomPk ? phantoms.find((phantom) => phantom.pk === currentPhantomPk) : null;

        return (
            <div>
                <h1>Upload Scan</h1>
                <form action={upload_scan_url} encType="multipart/form-data" method="post">
                    <input type="hidden" name="csrfmiddlewaretoken" value={csrftoken} />

                    <div>
                        {this.fieldErrors('machine')}

                        <label htmlFor="upload-scan-machine">Machine</label>
                        <select id="upload-scan-machine" name="machine" value={currentMachinePk} onChange={this.handleMachineChange.bind(this)} required>
                            <option value="" disabled />
                            {machines.map((machine) => <option value={machine.pk} key={machine.pk}>{machine.name}</option>)}
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
                        <select id="upload-scan-sequence" name="sequence" value={currentSequencePk} onChange={this.handleSequenceChange.bind(this)} required>
                            <option value="" disabled />
                            {sequences.map((sequence) => <option value={sequence.pk} key={sequence.pk}>{sequence.name}</option>)}
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
                        <select id="upload-scan-phantom" name="phantom" value={currentPhantomPk} onChange={this.handlePhantomChange.bind(this)} required>
                            <option value="" disabled />
                            {phantoms.map((phantom) => <option value={phantom.pk} key={phantom.pk}>{phantom.name}</option>)}
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
                        Please upload a zip-file containing the MRI DICOM files of a scan of the specified phatom, on the specified machine, using the specified sequence.
                    </div>

                    <div>
                        <label htmlFor="upload-scan-notes">Notes</label>
                        <textarea cols={40} rows={10} id="upload-scan-notes" name="notes" />
                    </div>

                    <a href={cancel_url}>Cancel</a>
                    <input type="submit" value="Process Scan" />
                </form>
            </div>
        );
    }
}

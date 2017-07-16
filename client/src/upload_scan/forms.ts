export interface IUploadScanForm {
    machine: '' | number;
    sequence: '' | number;
    phantom: '' | number;
    dicom_archive: File[];
    notes: string;
}

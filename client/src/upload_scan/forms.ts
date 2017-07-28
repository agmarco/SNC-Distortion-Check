export interface IUploadScanForm {
    machine: '' | number;
    sequence: '' | number;
    phantom: '' | number;
    dicom_archive: File[];
    dicom_archive_url: string;
    notes: string;
}

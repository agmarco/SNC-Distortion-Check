import React from 'react';
import format from 'date-fns/format';
import { connect } from 'react-redux';

import { IPhantomDto, IGoldenFiducialsDto } from 'common/service';
import { BoolIcon, AnchorForm, LoadingIcon } from 'common/components';

export interface IScanTableProps {
    phantom: IPhantomDto;
    goldenFiducialsSet?: IGoldenFiducialsDto[];
}

class GoldStandardTable extends React.Component<IScanTableProps, {}> {
    render() {
        let { phantom, goldenFiducialsSet } = this.props;
        goldenFiducialsSet = goldenFiducialsSet as IGoldenFiducialsDto[];

        return (
            <div>
                <div className="phantom-details">
                    <label>Model Number</label>
                    <p>{phantom.model_number}</p>
                    <label>Serial Number</label>
                    <p>{phantom.serial_number}</p>
                </div>
                <table className="cirs-table">
                    <thead>
                        <tr>
                            <th>Active</th>
                            <th>Date Uploaded</th>
                            <th>Type</th>
                            <th>Filename</th>
                            <th className="sep" />
                            <th colSpan={4}>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                    {goldenFiducialsSet.map((goldenFiducials) => (
                        <tr>
                            <td>
                                {goldenFiducials.is_active && <i className="fa fa-check success" aria-hidden="true" />}
                            </td>
                            <td>{format(goldenFiducials.created_on, 'MMMM D, YYYY')}</td>
                            <td>{goldenFiducials.type}</td>
                            <td>{goldenFiducials.type === 'CT' && goldenFiducials.dicom_series_filename}</td>
                            <td className="sep" />
                            {goldenFiducials.processing ?
                                <td colSpan={4}>The data is still being processed...</td> :
                                [
                                    <td className="action download-images">
                                        {goldenFiducials.type === 'CT' &&
                                        <a href={goldenFiducials.zipped_dicom_files_url as string}>
                                            Download Images
                                        </a>}
                                    </td>,
                                    <td className="action download-points">
                                        <a href={goldenFiducials.csv_url}>Download Points</a>
                                    </td>,
                                    <td className="action set-active">
                                        {!goldenFiducials.is_active && (
                                            <AnchorForm
                                                id={`activate-${goldenFiducials.pk}`}
                                                action={goldenFiducials.activate_url}
                                            >
                                                Set Active
                                            </AnchorForm>
                                        )}
                                    </td>,
                                    <td className="action delete">
                                        {!goldenFiducials.is_active && goldenFiducials.type !== 'CAD' && (
                                            <a href={goldenFiducials.delete_url}>
                                                <i className="fa fa-trash-o" aria-hidden="true" />
                                            </a>
                                        )}
                                    </td>,
                                ]}
                        </tr>
                    ))}
                    </tbody>
                </table>
                <div className="update-phantom-links">
                    <a href={phantom.upload_ct_url} className="btn tertiary">Upload Gold Standard CT</a>
                    <a href={phantom.upload_raw_url} className="btn tertiary">Upload Raw Points</a>
                </div>
            </div>
        );
    }
}

export default connect<any, any, any>((state: any) => ({goldenFiducialsSet: state.goldenFiducialsSet}))
    (GoldStandardTable as any);

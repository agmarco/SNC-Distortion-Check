import React from 'react';
import format from 'date-fns/format';
import { connect } from 'react-redux';

import { IPhantomDto, IGoldenFiducialsDto } from 'common/service';
import { BoolIcon, AnchorForm, LoadingIcon } from 'common/components';
import { IAppState } from '../reducers';

export interface IScanTableProps {
    phantom: IPhantomDto;
    pollCtError?: string | null;
    goldenFiducialsSet?: IGoldenFiducialsDto[];
}

class GoldStandardTable extends React.Component<IScanTableProps, {}> {
    renderGoldStandardActions(goldStandard: IGoldenFiducialsDto) {
        const { pollCtError } = this.props;

        if (goldStandard.processing) {
            if (pollCtError) {
                return (
                    <td colSpan={4}>
                        <span className="error">
                            Something went wrong. Please refresh the page to see if the gold standard has
                            {' '}
                            finished processing.
                        </span>
                    </td>
                );
            } else {
                return (
                    <td colSpan={4}>
                        The data is still being processed...
                        {' '}
                        <LoadingIcon />
                    </td>
                );
            }
        } else {
            return [
                <td key={0} className="action download-images">
                    {goldStandard.type === 'CT' &&
                    <a href={goldStandard.zipped_dicom_files_url as string}>
                        Download Images
                    </a>}
                </td>,
                <td key={1} className="action download-points">
                    <a href={goldStandard.csv_url}>Download Points</a>
                </td>,
                <td key={2} className="action set-active">
                    {!goldStandard.is_active && (
                        <AnchorForm
                            id={`activate-${goldStandard.pk}`}
                            action={goldStandard.activate_url}
                        >
                            Set Active
                        </AnchorForm>
                    )}
                </td>,
                <td key={3} className="action delete">
                    {!goldStandard.is_active && goldStandard.type !== 'CAD' && (
                        <a href={goldStandard.delete_url}>
                            <i className="fa fa-trash-o" aria-hidden="true" />
                        </a>
                    )}
                </td>,
            ];
        }
    }

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
                        <tr key={goldenFiducials.pk}>
                            <td>
                                {goldenFiducials.is_active && <i className="fa fa-check success" aria-hidden="true" />}
                            </td>
                            <td>{format(goldenFiducials.created_on, 'MMMM D, YYYY')}</td>
                            <td>{goldenFiducials.type}</td>
                            <td>{goldenFiducials.filename}</td>
                            <td className="sep" />
                            {this.renderGoldStandardActions(goldenFiducials)}
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

export default connect<any, any, any>((state: IAppState) => ({
    goldenFiducialsSet: state.goldenFiducialsSet,
    pollCtError: state.pollCtError,
}))(GoldStandardTable);

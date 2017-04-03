import * as React from 'react';

interface BoolIconProps {
    value: boolean;
}

export default ({ value }: BoolIconProps) => value ? <i className="fa fa-check" aria-hidden="true" /> : <i className="fa fa-times" aria-hidden="true" />

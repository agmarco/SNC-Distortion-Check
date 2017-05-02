import React from 'react';

interface IBoolIconProps {
    value: boolean;
}

export default ({ value }: IBoolIconProps) => {
    if (value) {
        return <i className="fa fa-check success" aria-hidden="true" />;
    } else {
        return <i className="fa fa-times error" aria-hidden="true" />;
    }
};

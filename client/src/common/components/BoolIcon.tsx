import React from 'react';
import classNames from 'classnames';

interface IBoolIconProps {
    value: boolean;
    title?: string;
}

export default ({ value, title }: IBoolIconProps) => {
    const classes = classNames(
        'fa',
        value ? 'fa-check' : 'fa-times',
        value ? 'success' : 'error',
    );

    return <i className={classes} aria-hidden="true" title={title} />;
};

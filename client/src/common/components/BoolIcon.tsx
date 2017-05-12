import React from 'react';
import classNames from 'classnames';

interface IBoolIconProps extends React.HTMLAttributes<HTMLElement> {
    success: boolean;
}

export default ({ success, ...iconAttributes }: IBoolIconProps) => {
    const classes = classNames(
        'fa',
        success ? ['fa-check', 'success'] : ['fa-times', 'error'],
        iconAttributes.className,
    );

    return <i className={classes} aria-hidden="true" {...iconAttributes} />;
};

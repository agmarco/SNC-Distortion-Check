import React from 'react';


interface IScrollableProps {
    start?: number;
    dx: number;
    clipPathId: string;
    children?: React.ReactNode;
}


export default (props: IScrollableProps) => {
    const { start = 0, dx, clipPathId, children } = props;

    return (
        <g clipPath={`url(#${clipPathId})`}>
            <g transform={`translate(${start + dx}, 0)`}>
                {children}
            </g>
        </g>
    );
};

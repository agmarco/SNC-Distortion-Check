import React from 'react';
import ReactDOM from 'react-dom';
import { AppContainer } from 'react-hot-loader';

import { IDjangoFormErrors } from './forms';


export const handleErrors = (res: Response, success: () => void) => {
    if (res.ok) {
        success();
    } else {
        throw new Error(res.statusText);
    }
};


// TODO handle arrays correctly according to application/x-www-form-urlencoded (?id[]=101404&id[]=7267261)
export const encode = (data: any) => {
    return Object.keys(data).map((key) => [key, data[key]].map(encodeURIComponent).join('=')).join('&');
};


export const renderApp = (Component: React.ComponentClass<any> | React.StatelessComponent<any>, appId: string) => {
    ReactDOM.render(
        <AppContainer>
            <Component />
        </AppContainer>,
        document.getElementById(appId),
    );
};


/**
 * Assume the array is already sorted.
 */
export const median = (sample: number[]) => {
    const i = Math.trunc(sample.length / 2);
    if (sample.length % 2 === 0) {
        return (sample[i - 1] + sample[i]) / 2;
    } else {
        return sample[i];
    }
};


export const quartiles = (sample: number[]) => {
    sample = [...sample].sort();
    const i = Math.trunc(sample.length / 2);
    let a = null;
    let b = null;
    if (sample.length % 2 === 0) {
        a = sample.slice(0, i);
        b = sample.slice(i);
    } else {
        a = sample.slice(0, i);
        b = sample.slice(i + 1);
    }
    return [median(a), median(sample), median(b)];
};

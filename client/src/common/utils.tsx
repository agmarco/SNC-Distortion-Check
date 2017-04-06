import * as React from 'react';
import * as ReactDOM from 'react-dom';
import { AppContainer } from 'react-hot-loader';

export const handleErrors = (res: Response, success: () => void) => {
    if (res.ok) {
        success();
    } else {
        throw new Error(res.statusText);
    }
};

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

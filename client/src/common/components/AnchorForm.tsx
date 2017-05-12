import React from 'react';

import CSRFToken from './CSRFToken';

interface IAnchorFormProps extends React.Attributes {
    action: string;
    children?: React.ReactNode;
}

export default class extends React.Component<IAnchorFormProps, {}> {
    form: HTMLFormElement;

    handleSubmit(event: React.FormEvent<HTMLAnchorElement>) {
        this.form.submit();
    }

    render() {
        const { action, children } = this.props;

        return (
            <form action={action} method="post" ref={(e) => this.form = e}>
                <CSRFToken />
                <a href="javascript:void(0)" onClick={this.handleSubmit.bind(this)}>
                    {children}
                </a>
            </form>
        );
    }
};

import React from 'react';
import { Dispatch } from 'redux';
import { connect } from 'react-redux';
import {
    Control,
    Errors,
    ErrorsProps,
    CustomComponentProps,
    ControlProps,
    Form,
    FormProps,
    actions,
    ErrorsObject,
} from 'react-redux-form';
import uniqueId from 'lodash/uniqueId';
import keyBy from 'lodash/keyBy';
import mapValues from 'lodash/mapValues';
import omit from 'lodash/omit';

export interface IDjangoData {
    [field: string]: any;
}

export interface IDjangoErrors {
    [field: string]: string[];
}

const ErrorsWrapper = (props: ErrorsProps & CustomComponentProps) => <ul className="errorlist">{props.children}</ul>;
const ErrorsComponent = (props: ErrorsProps & CustomComponentProps) => <li>{props.children}</li>;

export const CIRSErrors = (props: ErrorsProps) => {
    return <Errors wrapper={ErrorsWrapper} component={ErrorsComponent} {...props} />;
};

const controlProps = (props: ControlProps<any>) => {
    const { model } = props;

    let name;
    if (typeof model === 'string') {
        name = model.split('.').slice(-1)[0];
    }
    return {name, ...props};
};

export class CIRSControl<T> extends React.Component<ControlProps<T>, {}> {
    static custom = (props: ControlProps<any>) => <Control.custom {...controlProps(props)} />;
    static input = (props: ControlProps<any>) => <Control.input {...controlProps(props)} />;
    static text = (props: ControlProps<any>) => <Control.text {...controlProps(props)} />;
    static textarea = (props: ControlProps<any>) => <Control.textarea {...controlProps(props)} />;
    static radio = (props: ControlProps<any>) => <Control.radio {...controlProps(props)} />;
    static checkbox = (props: ControlProps<any>) => <Control.checkbox {...controlProps(props)} />;
    static file = (props: ControlProps<any>) => <Control.file {...controlProps(props)} />;
    static select = (props: ControlProps<any>) => <Control.select {...controlProps(props)} />;
    static reset = (props: ControlProps<any>) => <Control.reset {...controlProps(props)} />;

    render() {
        return <Control {...controlProps(this.props)} />;
    }
}

interface ICIRSFormProps extends FormProps {
    dispatch?: Dispatch<any>;
    djangoData?: IDjangoData;
    djangoErrors?: IDjangoErrors;
}

class CIRSFormImpl extends React.Component<ICIRSFormProps, {}> {
    constructor(props: ICIRSFormProps) {
        super();
        let { dispatch, djangoData, djangoErrors, model } = props;
        dispatch = dispatch as Dispatch<any>;

        if (typeof model === 'string') {
            if (djangoData) {
                for (let field of Object.keys(djangoData)) {
                    dispatch(actions.change(`${model}.${field}`, djangoData[field]));
                }
            }

            if (djangoErrors) {
                if (djangoErrors.__all__) {
                    const formErrors = keyBy<string>(djangoErrors.__all__, s => uniqueId());
                    dispatch(actions.setErrors(model, formErrors));
                }

                const fieldErrors = mapValues<string[], ErrorsObject>(
                    omit<IDjangoErrors, IDjangoErrors>(djangoErrors, '__all__'),
                    a => keyBy<string>(a, s => uniqueId()),
                );
                for (let field of Object.keys(fieldErrors)) {
                    dispatch(actions.setErrors(`${model}.${field}`, fieldErrors[field]));
                }
            }
        }
    }

    render() {
        const { dispatch, djangoData, djangoErrors, ...formProps } = this.props;
        return <Form {...formProps} />;
    }
}

// TODO figure out the types
export const CIRSForm = connect()(CIRSFormImpl as any);

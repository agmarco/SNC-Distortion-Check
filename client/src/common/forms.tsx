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

export interface IDjangoFormData {
    [field: string]: any;
}

export interface IDjangoFormErrors {
    [field: string]: string[];
}

const ErrorsWrapper = (props: ErrorsProps & CustomComponentProps) => <ul className="errorlist">{props.children}</ul>;
const ErrorsComponent = (props: ErrorsProps & CustomComponentProps) => <li>{props.children}</li>;

interface ICirsErrorsProps extends ErrorsProps {
    required?: boolean;
    email?: boolean;
}

export const CirsErrors = (props: ICirsErrorsProps) => {
    const { required, email, messages = {}, ...rest } = props;

    if (required) {
        messages.required = "This field is required.";
    }

    if (email) {
        messages.isEmail = "Please enter a valid email address.";
    }

    return (
        <Errors
            wrapper={ErrorsWrapper}
            component={ErrorsComponent}
            messages={messages}
            show={{touched: true}}
            {...rest}
        />
    );
};

// Make the field name attribute equal to the last component of the field model
const controlProps = (props: ControlProps<any>) => {
    const { model, required, type, validators = {}, validateOn = "blur", ...rest } = props;

    let name;
    if (typeof model === 'string') {
        name = model.split('.').slice(-1)[0];
    }

    if (required) {
        validators.required = (value: any) => value !== null && value !== '';
    }

    if (type === 'email') {
        const emailRegex = /^[a-zA-Z0-9.!#$%&’*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$/;
        validators.isEmail = (value: any) => value !== null && value.match(emailRegex);
    }

    return {name, model, required, type, validators, validateOn, formNoValidate: true, ...rest};
};

export class CirsControl<T> extends React.Component<ControlProps<T>, {}> {
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

interface ICirsFormProps extends FormProps {
    dispatch?: Dispatch<any>;
    djangoData?: IDjangoFormData;
    djangoErrors?: IDjangoFormErrors;
}

class CirsFormImpl extends React.Component<ICirsFormProps, {}> {
    componentDidMount() {
        const { dispatch, djangoData, djangoErrors, model } = this.props;

        if (dispatch && typeof model === 'string') {

            // Populate form with initial data. Assumes the field model names are the same as the Django field names.
            if (djangoData) {
                for (let field of Object.keys(djangoData)) {
                    dispatch(actions.change(`${model}.${field}`, djangoData[field]));
                }
            }

            // Display errors from Django. Assumes the field model names are the same as the Django field names.
            if (djangoErrors) {
                if (djangoErrors.__all__) {
                    const formErrors = keyBy<string>(djangoErrors.__all__, s => `django${uniqueId()}`);
                    dispatch(actions.setErrors('_', formErrors));
                    dispatch(actions.setTouched('_'));
                }

                const fieldErrors = mapValues<string[], ErrorsObject>(
                    omit<IDjangoFormErrors, IDjangoFormErrors>(djangoErrors, '__all__'),
                    a => keyBy<string>(a, s => `django${uniqueId()}`),
                );
                for (let field of Object.keys(fieldErrors)) {
                    const fieldModel = `${model}.${field}`;
                    dispatch(actions.setErrors(fieldModel, fieldErrors[field]));
                    dispatch(actions.setTouched(fieldModel));
                }
            }
        }
    }

    render() {
        const { dispatch, djangoData, djangoErrors, ...rest } = this.props;
        return <Form {...rest} />;
    }
}

export const CirsForm = connect()(CirsFormImpl as any);

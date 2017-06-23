import { combineReducers } from 'redux';
import { handleActions } from 'redux-actions';
import { combineForms, FormState } from 'react-redux-form';

import { ICreatePhantomForm } from './forms';
import * as constants from './constants';


export declare const FORM_INITIAL: ICreatePhantomForm;


export interface IAppState {
    serialNumberInfo: ISerialNumberInfoState[];
    forms: {
        forms: {
            phantom: FormState;
        };
        phantom: ICreatePhantomForm;
    };
}


export interface ISerialNumberInfoState {
    message: string | null;
    modelNumber: string | null;
}


const serialNumberInfoReducer = handleActions<ISerialNumberInfoState, any>({
    [constants.UPDATE_SERIAL_NUMBER_INFO]: (state, action) => ({...state, ...action.payload}),
}, {
    message: null,
    modelNumber: null,
});


export default combineReducers({
    serialNumberInfo: serialNumberInfoReducer,
    forms: combineForms({
        phantom: FORM_INITIAL,
    }, 'forms'),
});

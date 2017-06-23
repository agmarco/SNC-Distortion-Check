import { combineReducers } from 'redux';
import { handleActions } from 'redux-actions';
import { combineForms } from 'react-redux-form';

import { CirsFormState } from 'common/forms';
import { IRegisterForm } from './forms';
import * as constants from './constants';


export declare const FORM_INITIAL: IRegisterForm;


export interface IAppState {
    serialNumberInfo: ISerialNumberInfoState[];
    forms: CirsFormState<IFormModelState>;
}


interface IFormModelState {
    register: IRegisterForm;
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
        register: FORM_INITIAL,
    }, 'forms'),
});
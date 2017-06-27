import { Action } from 'redux-actions';
import { call, put, all, takeEvery } from 'redux-saga/effects';
import { actions as formActions } from 'react-redux-form';

import * as constants from './constants';
import * as actions from './actions';
import * as api from './api';

function* getSerialNumberValidity(action: Action<string>): any {
    const response = yield api.validateSerial({serial_number: action.payload});

    if (response.ok) {
        const { valid, model_number, message } = yield call(response.json.bind(response));
        yield put(actions.updateSerialNumberInfo({
            message,
            modelNumber: model_number,
        }));
        yield put(formActions.setValidity('forms.register.phantom_serial_number', valid));
    }
}

function* validateSerialNumber(): any {
    yield takeEvery(constants.VALIDATE_SERIAL_NUMBER, getSerialNumberValidity);
}

export default function* () {
    yield all([
        validateSerialNumber(),
    ]);
};

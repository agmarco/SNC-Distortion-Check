import { Action } from 'redux-actions';
import { call, put, all, takeLatest } from 'redux-saga/effects';
import { actions as formActions } from 'react-redux-form';

import * as api from 'common/api';
import * as constants from './constants';
import * as actions from './actions';

function* getSerialNumberValidity(action: Action<string>): any {
    try {
        const response = yield call(api.addOkCheck(api.validateSerial), {serial_number: action.payload});
        const { valid, model_number, message } = yield call(response.json.bind(response));
        yield put(actions.updateSerialNumberInfo({
            message,
            modelNumber: model_number,
        }));
        yield put(formActions.setValidity('forms.phantom.serial_number', valid));
    } catch (error) {
        yield put(formActions.setValidity('forms.phantom.serial_number', false));
    }
}

function* validateSerialNumber(): any {
    yield takeLatest(constants.VALIDATE_SERIAL_NUMBER, getSerialNumberValidity);
}

export default function* () {
    yield all([
        validateSerialNumber(),
    ]);
};

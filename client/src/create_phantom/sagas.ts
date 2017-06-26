import * as Cookies from 'js-cookie';
import { Action } from 'redux-actions';
import { call, put, all, takeLatest } from 'redux-saga/effects';
import { actions as formActions } from 'react-redux-form';

import { encode } from 'common/utils';
import * as constants from './constants';
import * as actions from './actions';


declare const VALIDATE_SERIAL_URL: string;


function* getSerialNumberValidity(action: Action<string>): any {
    const response = yield call(fetch, VALIDATE_SERIAL_URL, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': Cookies.get('csrftoken'),
        },
        body: encode({serial_number: action.payload}),
    });

    if (response.ok) {
        const { valid, model_number, message } = yield call(response.json.bind(response));
        yield put(actions.updateSerialNumberInfo({
            message,
            modelNumber: model_number,
        }));
        yield put(formActions.setValidity('forms.phantom.serial_number', valid));
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

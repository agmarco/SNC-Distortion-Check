import * as Cookies from 'js-cookie';
import { call, put, all, take, cancel, fork } from 'redux-saga/effects';
import { actions as formActions } from 'react-redux-form';

import { encode } from 'common/utils';
import * as constants from './constants';
import * as actions from './actions';

declare const VALIDATE_SERIAL_URL: string;

function* getSerialNumberValidity(serialNumber: string): any {
    const response = yield call(fetch, VALIDATE_SERIAL_URL, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': Cookies.get('csrftoken'),
        },
        body: encode({serial_number: serialNumber}),
    });

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
    let getSerialNumberValidityTask;

    while (true) {
        const validateSerialNumberAction = yield take(constants.VALIDATE_SERIAL_NUMBER);
        if (getSerialNumberValidityTask) {
            yield cancel(getSerialNumberValidityTask);
        }
        getSerialNumberValidityTask = yield fork(getSerialNumberValidity, validateSerialNumberAction.payload);
    }
}

export default function* () {
    yield all([
        validateSerialNumber(),
    ]);
};

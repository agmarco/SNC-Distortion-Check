import { delay } from 'redux-saga';
import { call, race, CallEffect } from 'redux-saga/effects';


export function* addTimeout(apiOuter: CallEffect) {
    return call(function* (api: CallEffect) {
        const {response} = yield race({
            response: api,
            timeout: call(delay, 5000),
        });

        if (response) {
            return response;
        } else {
            throw new Error("Request timeout");
        }
    }, apiOuter);
}


export function* addOkCheck(apiOuter: CallEffect) {
    return call(function* (api: CallEffect) {
        const response = yield api;

        if (response.ok) {
            return response;
        } else {
            throw new Error(response.statusText);
        }
    }, apiOuter);
}

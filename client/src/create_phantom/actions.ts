import { createAction } from 'redux-actions';

import { ISerialNumberInfoState } from './reducers';
import * as constants from './constants';


export const updateSerialNumberInfo = createAction<ISerialNumberInfoState>(constants.UPDATE_SERIAL_NUMBER_INFO);


export const validateSerialNumber = createAction<string>(constants.VALIDATE_SERIAL_NUMBER);

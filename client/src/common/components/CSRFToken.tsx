import * as React from 'react';
import * as Cookies from 'js-cookie';

export default () => {
    return <input type="hidden" name="csrfmiddlewaretoken" value={Cookies.get('csrftoken')} />;
};

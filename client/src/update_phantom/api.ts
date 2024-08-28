import * as Cookies from 'js-cookie';

declare const POLL_CT_URL: string;

export const pollCt = (body: any) => {
    return fetch(POLL_CT_URL, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': Cookies.get('csrftoken'),
        },
        body: JSON.stringify(body),
    });
};

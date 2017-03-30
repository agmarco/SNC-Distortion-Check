export const handleErrors = (res: Response, success: () => void) => {
    if (res.ok) {
        success();
    } else {
        throw new Error(res.statusText)
    }
};

export const encode = (data: any) => {
    return Object.keys(data).map((key) => [key, data[key]].map(encodeURIComponent).join('=')).join('&');
};

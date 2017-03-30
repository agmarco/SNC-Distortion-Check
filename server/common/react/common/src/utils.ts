export const handleErrors = (res: Response, success: () => void) => {
    if (res.ok) {
        success();
    } else {
        throw new Error(res.statusText)
    }
};

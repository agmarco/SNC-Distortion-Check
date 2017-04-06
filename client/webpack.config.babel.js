import webpackDev from './webpack.config.dev.babel';
import webpackProd from './webpack.config.prod.babel';

export default (env) => {
    if (['dev', 'hot'].includes(env)) {
        return webpackDev(env);
    } else if (env === 'prod') {
        return webpackProd(env);
    }
}

export default (env) => {
    if (['dev', 'hot'].includes(env)) {
        return require('./webpack.config.dev.babel').default(env);
    } else if (env === 'test') {
        return require('./webpack.config.test.babel').default(env);
    } else if (env === 'prod') {
        return require('./webpack.config.prod.babel').default(env);
    }
}

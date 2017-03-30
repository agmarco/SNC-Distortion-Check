import gulp from 'gulp';
import gutil from 'gulp-util';
import webpack from 'webpack';
import WebpackDevServer from 'webpack-dev-server';

import webpackDevFactory from './webpack.config.dev.babel';
import webpackProd from './webpack.config.prod.babel';

const webpackStats = {
    chunks: false,
    colors: true,
};

gulp.task('default', ['dev']);

gulp.task('dev', ['dev:webpack-dev-server']);

gulp.task('prod', ['prod:webpack']);

gulp.task('dev:webpack', (cb) => {
    webpack(webpackDevFactory({hot: false})).run((err, stats) => {
        if (err) throw new gutil.PluginError('dev:webpack', err);
        gutil.log(stats.toString(webpackStats));
        cb();
    });
});

gulp.task('dev:webpack:watch', (cb) => {
    let firstRun = true;
    webpack(webpackDevFactory({hot: false})).watch(300, (err, stats) => {
        if (err) throw new gutil.PluginError('webpack:watch', err);
        gutil.log(stats.toString(webpackStats));
        if (firstRun) {
            firstRun = false;
            cb();
        }
    });
});

gulp.task('dev:webpack-dev-server', (cb) => {
    const webpackDev = webpackDevFactory({hot: true});
    new WebpackDevServer(webpack(webpackDev), {
        publicPath: webpackDev.output.publicPath,
        contentBase: 'src',
        hot: true,
        stats: webpackStats,
    }).listen(8080, '0.0.0.0', (err) => {
        if (err) throw new gutil.PluginError('dev:webpack-dev-server', err);
        cb();
    });
});

gulp.task('prod:webpack', (cb) => {
    webpack(webpackProd).run((err, stats) => {
        if (err) throw new gutil.PluginError('webpack', err);
        gutil.log(stats.toString(webpackStats));
        cb();
    });
});

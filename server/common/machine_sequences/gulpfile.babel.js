import gulp from 'gulp';
import gutil from 'gulp-util';
import webpack from 'webpack';

import webpackDev from './webpack.config.dev.babel';
import webpackProd from './webpack.config.prod.babel';

const webpackStats = {
    chunks: false,
    colors: true,
};

gulp.task('default', ['prod']);

gulp.task('dev', ['webpack:watch']);

gulp.task('prod', ['webpack']);

gulp.task('webpack', (cb) => {
    webpack(webpackProd).run((err, stats) => {
        if (err) throw new gutil.PluginError('webpack', err);
        gutil.log(stats.toString(webpackStats));
        cb();
    });
});

gulp.task('webpack:watch', (cb) => {
    let firstRun = true;
    webpack(webpackDev).watch(300, (err, stats) => {
        if (err) throw new gutil.PluginError('webpack:watch', err);
        gutil.log(stats.toString(webpackStats));
        if (firstRun) {
            firstRun = false;
            cb();
        }
    });
});

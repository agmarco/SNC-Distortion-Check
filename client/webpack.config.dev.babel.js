import * as path from 'path';
import * as webpack from 'webpack';
import ExtractTextPlugin from 'extract-text-webpack-plugin';
import StyleLintPlugin from 'stylelint-webpack-plugin';
import merge from 'webpack-merge';

import webpackBase from './webpack.config.base.babel';

export default (env) => {
    const config = merge(webpackBase(env), {
        output: {
            publicPath: 'http://0.0.0.0:8080/',
            filename: '[name].js',
        },

        devtool: 'cheap-eval-source-map',

        plugins: [
            new webpack.optimize.CommonsChunkPlugin({
                name: 'vendor',
                minChunks: Infinity,
            }),
            new ExtractTextPlugin('[name].css'),
            new StyleLintPlugin(),
        ],

        module: {
            rules: [
                {
                    test: /\.tsx?$/,
                    exclude: /node_modules/,
                    enforce: 'pre',
                    loader: 'tslint-loader',
                },
            ],
        },

        devServer: {
            hotOnly: env === 'hot',
            contentBase: path.join(__dirname, 'dist'),
            publicPath: 'http://0.0.0.0:8080/',
            compress: true,
            host: '0.0.0.0',
            port: 8080,
            stats: {chunks: false},
        },
    });

    if (env === 'hot') {
        for (let bundle of Object.values(config.entry)) {
            bundle.unshift(`webpack-dev-server/client?${config.devServer.publicPath}`);
        }
        config.plugins.push(
            new webpack.HotModuleReplacementPlugin(),
            new webpack.NamedModulesPlugin(),
        );
    }

    return config;
}

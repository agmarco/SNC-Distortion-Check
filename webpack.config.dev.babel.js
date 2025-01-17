import * as path from 'path';
import * as webpack from 'webpack';
import ExtractTextPlugin from 'extract-text-webpack-plugin';
import StyleLintPlugin from 'stylelint-webpack-plugin';
import merge from 'webpack-merge';

import webpackBase from './webpack.config.base.babel';


// TODO HMR broken - https://github.com/reactjs/react-redux/releases/tag/v2.0.0
// TODO too much junk in the HMR output
export default (env) => {
    const config = merge(webpackBase(env), {
        output: {
            // TODO: grab this from the .env file
            publicPath: env === 'hot' ? 'http://0.0.0.0:8080/' : 'http://0.0.0.0:8000/app/static/',
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
            contentBase: path.join(__dirname, 'client/dist'),
            publicPath: 'http://0.0.0.0:8080/',
            compress: true,
            host: '0.0.0.0',
            port: 8080,
            stats: {chunks: false},
            headers: {'Access-Control-Allow-Origin': '*'},
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

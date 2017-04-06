import * as path from 'path';
import * as webpack from 'webpack';
import ManifestPlugin from 'webpack-manifest-plugin';
import ChunkManifestPlugin from 'chunk-manifest-webpack-plugin';
import WebpackChunkHash from 'webpack-chunk-hash';

export default (env) => ({
    entry: {
        app: [
            'babel-polyfill',
            'react-hot-loader/patch',
            path.join(__dirname, 'src/app.tsx'),
        ],
        vendor: [
            'react-hot-loader',
            'react',
            'react-dom',
        ],
    },

    output: {
        path: path.join(__dirname, '../dist/upload_scan'),
        filename: '[name].[chunkhash].js',
        chunkFilename: '[name].[chunkhash].js',
    },

    devtool: 'cheap-module-source-map',

    plugins: [
        new webpack.NoEmitOnErrorsPlugin(),
        new webpack.LoaderOptionsPlugin({minimize: true, debug: false}),
        // TODO throwing error
        //new webpack.optimize.UglifyJsPlugin({
        //    sourceMap: true,
        //    beautify: false,
        //    mangle: {screw_ie8: true, keep_fnames: true},
        //    compress: {screw_ie8: true},
        //    comments: false,
        //}),
        new webpack.HashedModuleIdsPlugin(),
        new webpack.optimize.CommonsChunkPlugin({
            name: ['vendor', 'manifest'],
            minChunks: Infinity,
        }),
        new ManifestPlugin(),
        new ChunkManifestPlugin({
            filename: 'chunk-manifest.json',
            manifestVariable: 'webpackManifest',
        }),
        new WebpackChunkHash(),
        new webpack.DefinePlugin({
            'process.env.NODE_ENV': JSON.stringify('production'),
        })
    ],

    module: {
        rules: [
            {
                test: /\.tsx?$/,
                use: ['babel-loader', 'ts-loader'],
            }, {
                test: /\.scss$/,
                use: ['style-loader', 'css-loader', 'sass-loader'],
            },
        ],
    },

    resolve: {
        modules: [
            path.join(__dirname, 'src'),
            path.join(__dirname, '..'),
            path.join(__dirname, '../node_modules'),
        ],
        extensions: ['.webpack.js', '.web.js', '.js', '.jsx', '.ts', '.tsx'],
    },
});

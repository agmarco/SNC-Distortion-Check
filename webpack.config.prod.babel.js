import * as webpack from 'webpack';
import ManifestPlugin from 'webpack-manifest-plugin';
import ChunkManifestPlugin from 'chunk-manifest-webpack-plugin';
import WebpackChunkHash from 'webpack-chunk-hash';
import ExtractTextPlugin from 'extract-text-webpack-plugin';
import merge from 'webpack-merge';

import webpackBase from './webpack.config.base.babel';

export default (env) => merge(webpackBase(env), {
    output: {
        filename: '[name].[chunkhash].js',
        chunkFilename: '[name].[chunkhash].js',
    },

    devtool: 'cheap-module-source-map',

    plugins: [
        new webpack.HashedModuleIdsPlugin(),
        new webpack.LoaderOptionsPlugin({minimize: true}),
        new webpack.optimize.UglifyJsPlugin({sourceMap: true}),
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
        }),
        new ExtractTextPlugin('[name].[contenthash].css'),
    ],
});

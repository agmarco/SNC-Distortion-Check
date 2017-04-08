import * as path from 'path';
import * as webpack from 'webpack';
import ManifestPlugin from 'webpack-manifest-plugin';
import ChunkManifestPlugin from 'chunk-manifest-webpack-plugin';
import WebpackChunkHash from 'webpack-chunk-hash';
import ExtractTextPlugin from 'extract-text-webpack-plugin';

export default (env) => ({
    entry: {
        vendor: [
            'babel-polyfill',
            'react-hot-loader/patch',
            'react-hot-loader',
            'react',
            'react-dom',
        ],
        landing: [path.join(__dirname, 'src/landing/app.tsx')],
        machine_sequences: [path.join(__dirname, 'src/machine_sequences/app.tsx')],
        machine_sequence_detail: [path.join(__dirname, 'src/machine_sequence_detail/app.tsx')],
        add_phantom: [path.join(__dirname, 'src/add_phantom/app.tsx')],
        upload_scan: [path.join(__dirname, 'src/upload_scan/app.tsx')],
        base: [path.join(__dirname, 'src/base/app.scss')],
    },

    output: {
        path: path.join(__dirname, 'dist'),
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
        }),
        new ExtractTextPlugin({filename: '[name].[chunkhash].css', allChunks: true}),
    ],

    module: {
        rules: [
            {
                test: /\.tsx?$/,
                use: ['babel-loader', 'ts-loader'],
                exclude: /node_modules/,
            }, {
                test: /\.scss$/,
                use: ExtractTextPlugin.extract({
                    fallback: 'style-loader',
                    use: ['css-loader', 'sass-loader']
                }),
            },
        ],
    },

    resolve: {
        modules: [
            path.join(__dirname, 'src'),
            path.join(__dirname, 'node_modules'),
        ],
        extensions: ['.webpack.js', '.web.js', '.js', '.jsx', '.ts', '.tsx'],
    },
});

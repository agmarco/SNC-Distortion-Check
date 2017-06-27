import * as path from 'path';
import * as webpack from 'webpack';
import ExtractTextPlugin from 'extract-text-webpack-plugin';

export default (env) => ({
    entry: {
        vendor: [
            'babel-polyfill',
            'react-hot-loader/patch',
            'react-hot-loader',
            'react',
            'react-dom',
            'isomorphic-fetch',
        ],
        landing: [path.join(__dirname, 'client/src/landing/app.tsx')],
        machine_sequence_detail: [path.join(__dirname, 'client/src/machine_sequence_detail/app.tsx')],
        create_phantom: [path.join(__dirname, 'client/src/create_phantom/app.tsx')],
        update_phantom: [path.join(__dirname, 'client/src/update_phantom/app.tsx')],
        upload_scan: [path.join(__dirname, 'client/src/upload_scan/app.tsx')],
        register: [path.join(__dirname, 'client/src/register/app.tsx')],

        // CSS only:
        base: [path.join(__dirname, 'client/src/base/app.scss')],
        login: [path.join(__dirname, 'client/src/login/app.scss')],
        configuration: [path.join(__dirname, 'client/src/configuration/app.scss')],
        dicom_overlay: [path.join(__dirname, 'client/src/dicom_overlay/app.scss')],
    },

    output: {
        path: path.join(__dirname, 'client/dist'),
    },

    plugins: [
        new webpack.NoEmitOnErrorsPlugin(),
    ],

    module: {
        rules: [
            {
                test: /\.tsx?$/,
                exclude: /node_modules/,
                use: ['babel-loader', 'ts-loader'],
            }, {

                // TODO HMR CSS
                // TODO don't include the base CSS in the other chunks
                test: /\.scss$/,
                use: ExtractTextPlugin.extract({
                    fallback: 'style-loader',
                    use: ['css-loader', 'sass-loader'],
                }),
            }, {
                test: /\.(svg)$/,
                loader: 'svg-url-loader',
            }, {
                test: /\.(ico|jpg|png|gif|eot|otf|webp|ttf|woff|woff2)$/,
                loader: 'url-loader',
                query: {limit: 8192},
            },
        ],
    },

    resolve: {
        modules: [
            path.join(__dirname, 'client/src'),
            path.join(__dirname, 'node_modules'),
        ],
        extensions: ['.webpack.js', '.web.js', '.js', '.jsx', '.ts', '.tsx'],
    },
});

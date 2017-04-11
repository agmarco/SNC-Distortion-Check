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
        ],
        landing: [path.join(__dirname, 'src/landing/app.tsx')],
        machine_sequences: [path.join(__dirname, 'src/machine_sequences/app.tsx')],
        machine_sequence_detail: [path.join(__dirname, 'src/machine_sequence_detail/app.tsx')],
        add_phantom: [path.join(__dirname, 'src/add_phantom/app.tsx')],
        upload_scan: [path.join(__dirname, 'src/upload_scan/app.tsx')],

        // CSS only:
        base: [path.join(__dirname, 'src/base/app.scss')],
        login: [path.join(__dirname, 'src/login/app.scss')],
        configuration: [path.join(__dirname, 'src/configuration/app.scss')],
    },

    output: {
        path: path.join(__dirname, 'dist'),
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

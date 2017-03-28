import * as path from 'path';
import * as webpack from 'webpack';

export default ({
    entry: {
        'app': [
            'babel-polyfill',
            path.resolve('./src/app.tsx'),
        ],
        'vendor': [
            'webpack-dev-server/client?http://0.0.0.0:8080',
            'webpack/hot/only-dev-server',
            'react-hot-loader/patch',
            'react-hot-loader',
            'react',
            'react-dom',
        ],
    },

    output: {
        path: path.resolve('../static/common/machine_sequences'),
        publicPath: 'http://0.0.0.0:8080/common/machine_sequences/',
    },

    devtool: 'eval',

    plugins: [
        new webpack.NoEmitOnErrorsPlugin(),
        new webpack.optimize.CommonsChunkPlugin({name: 'vendor', filename: '[name].js'}),
        new webpack.NamedModulesPlugin(),
        new webpack.HotModuleReplacementPlugin(),
    ],

    module: {
        rules: [
            {
                test: /\.tsx?$/,
                use: [
                    {loader: 'babel-loader', options: {
                        presets: [['es2015', {modules: false}], 'stage-0', 'react'],
                    }},
                    {loader: 'ts-loader'},
                ],
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

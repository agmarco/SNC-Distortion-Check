import * as path from 'path';
import * as webpack from 'webpack';

export default ({
    entry: {
        'app': [
            'babel-polyfill',
            path.resolve('./src/app.tsx'),
        ],
        'vendor': [
            'react-hot-loader/patch',
            'react-hot-loader',
            'react',
            'react-dom',
        ],
    },

    output: {
        path: path.resolve('../static/common/machine_sequences'),
    },

    devtool: 'source-map',

    plugins: [
        new webpack.NoEmitOnErrorsPlugin(),
        new webpack.optimize.CommonsChunkPlugin({name: 'vendor', filename: '[name].js'}),
        new webpack.optimize.UglifyJsPlugin({sourceMap: true}),
        new webpack.LoaderOptionsPlugin({minimize: true}),
        new webpack.DefinePlugin({'process.env': {'NODE_ENV': JSON.stringify('production')}}),
        new ExtractTextPlugin({filename: '[name].css', allChunks: true}),
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
            }, {
                test: /\.scss$/,
                use: ExtractTextPlugin.extract({use: 'css-loader!sass-loader', fallback: 'style-loader'}),
            }, {
                test: /\.(ico|jpg|png|gif|eot|otf|webp|svg|ttf|woff|woff2)$/,
                use: {
                    loader: 'url-loader',
                    options: {limit: 8192},
                },
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

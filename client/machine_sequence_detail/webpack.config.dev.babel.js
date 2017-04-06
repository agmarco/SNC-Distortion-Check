import * as path from 'path';
import * as webpack from 'webpack';

export default (env) => {
    const config = {
        entry: {
            app: [
                'babel-polyfill',
                'react-hot-loader/patch',
                path.join(__dirname, 'src/box.js'),
                path.join(__dirname, 'src/app.tsx'),
            ],
            vendor: [
                'react-hot-loader',
                'react',
                'react-dom',
                'd3',
            ],
        },

        output: {
            path: path.join(__dirname, '../dist/machine_sequence_detail'),
            publicPath: 'http://0.0.0.0:8080/machine_sequence_detail/',
            filename: '[name].js',
        },

        devtool: 'cheap-eval-source-map',

        plugins: [
            new webpack.NoEmitOnErrorsPlugin(),
            new webpack.optimize.CommonsChunkPlugin({name: 'vendor'}),
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

        devServer: {
            hot: env === 'hot',
            contentBase: path.join(__dirname, '../dist/machine_sequence_detail'),
            publicPath: 'http://0.0.0.0:8080/machine_sequence_detail/',
            compress: true,
            host: '0.0.0.0',
            port: 8080,
            stats: {chunks: false},
        },
    };

    if (env === 'hot') {
        config.entry.app.unshift(
            'webpack-dev-server/client?http://0.0.0.0:8080',
            'webpack/hot/only-dev-server',
        );
        config.plugins.push(
            new webpack.HotModuleReplacementPlugin(),
            new webpack.NamedModulesPlugin(),
        );
    }

    return config;
}

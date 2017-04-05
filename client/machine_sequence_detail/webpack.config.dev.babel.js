import * as path from 'path';
import * as webpack from 'webpack';

export default (options) => {
    const config = {
        entry: {
            app: [
                'babel-polyfill',
                'react-hot-loader/patch',
                path.resolve('./src/app.tsx'),
            ],
            vendor: [
                'react-hot-loader',
                'react',
                'react-dom',
            ],
        },

        output: {
            path: path.resolve('../dist/machine_sequence_detail'),
            publicPath: 'http://0.0.0.0:8080/machine_sequence_detail/',
        },

        devtool: 'eval',

        plugins: [
            new webpack.NoEmitOnErrorsPlugin(),
            new webpack.optimize.CommonsChunkPlugin({name: 'vendor', filename: '[name].js'}),
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
                path.resolve('./src'),
                path.resolve('../'),
                path.resolve('../node_modules'),
            ],
            extensions: ['.webpack.js', '.web.js', '.js', '.jsx', '.ts', '.tsx'],
        },
    };

    if (options.hot) {
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

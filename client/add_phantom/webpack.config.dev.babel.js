import * as path from 'path';
import * as webpack from 'webpack';

export default (options) => {
    const config = {
        entry: {
            app: [
                'babel-polyfill',
                path.resolve('./src/app.tsx'),
            ],
            vendor: [
                'react-hot-loader/patch',
                'react-hot-loader',
                'react',
                'react-dom',
            ],
        },

        output: {
            path: path.resolve('../dist/add_phantom'),
            publicPath: 'http://0.0.0.0:8080/add_phantom/',
        },

        devtool: 'eval',

        plugins: [
            new webpack.NoEmitOnErrorsPlugin(),
            new webpack.optimize.CommonsChunkPlugin({name: 'vendor', filename: '[name].js'}),
            new webpack.NamedModulesPlugin(),
        ],

        module: {
            rules: [
                {
                    test: /\.tsx?$/,
                    use: [
                        {
                            loader: 'babel-loader',
                            options: {
                                presets: [['es2015', {modules: false}], 'react'],
                                plugins: ['react-hot-loader/babel'],
                            },
                        },
                        {loader: 'ts-loader'},
                    ],
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
        config.entry.vendor.unshift(
            'webpack-dev-server/client?http://0.0.0.0:8080',
            'webpack/hot/only-dev-server',
        );
        config.plugins.push(new webpack.HotModuleReplacementPlugin());
    }

    return config;
};

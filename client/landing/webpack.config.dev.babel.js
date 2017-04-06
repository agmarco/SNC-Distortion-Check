import * as path from 'path';
import * as webpack from 'webpack';

export default (env) => {
    const config = {
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
            path: path.join(__dirname, '../dist/landing'),
            publicPath: 'http://0.0.0.0:8080/landing/',
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
                    enforce: 'pre',
                    loader: 'tslint-loader',
                }, {
                    test: /\.tsx?$/,
                    use: ['babel-loader', 'ts-loader'],
                    exclude: /node_modules/,
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
            hotOnly: env === 'hot',
            contentBase: path.join(__dirname, '../dist/landing'),
            publicPath: 'http://0.0.0.0:8080/landing/',
            compress: true,
            host: '0.0.0.0',
            port: 8080,
            stats: {chunks: false},
        },
    };

    if (env === 'hot') {
        config.entry.app.unshift(
            'webpack-dev-server/client?http://0.0.0.0:8080',
        );
        config.plugins.push(
            new webpack.HotModuleReplacementPlugin(),
            new webpack.NamedModulesPlugin(),
        );
    }

    return config;
}

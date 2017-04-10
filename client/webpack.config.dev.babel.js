import * as path from 'path';
import * as webpack from 'webpack';
import ExtractTextPlugin from 'extract-text-webpack-plugin';
import StyleLintPlugin from 'stylelint-webpack-plugin';

export default (env) => {
    const config = {
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
            publicPath: 'http://0.0.0.0:8080/',
            filename: '[name].js',
        },

        devtool: 'cheap-eval-source-map',

        plugins: [
            new webpack.NoEmitOnErrorsPlugin(),
            new webpack.optimize.CommonsChunkPlugin({
                name: 'vendor',
                minChunks: Infinity,
            }),
            new ExtractTextPlugin('[name].css'),
            new StyleLintPlugin(),
        ],

        module: {
            rules: [
                {
                    test: /\.tsx?$/,
                    exclude: /node_modules/,
                    enforce: 'pre',
                    loader: 'tslint-loader',
                }, {
                    test: /\.tsx?$/,
                    exclude: /node_modules/,
                    use: ['babel-loader', 'ts-loader'],
                }, {
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

        devServer: {
            hotOnly: env === 'hot',
            contentBase: path.join(__dirname, 'dist'),
            publicPath: 'http://0.0.0.0:8080/',
            compress: true,
            host: '0.0.0.0',
            port: 8080,
            stats: {chunks: false},
        },
    };

    if (env === 'hot') {
        for (let bundle of Object.values(config.entry)) {
            bundle.unshift(`webpack-dev-server/client?${config.devServer.publicPath}`);
        }
        config.plugins.push(
            new webpack.HotModuleReplacementPlugin(),
            new webpack.NamedModulesPlugin(),
        );
    }

    return config;
}

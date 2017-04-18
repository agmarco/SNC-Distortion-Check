import * as path from 'path';

// Some externals are for enzyme, see:
// https://github.com/airbnb/enzyme/issues/47

// TODO according to enzyme, we shouldn't need react-addons-test-utils since we're using React >= 15.5
// but the tests throw an error without it

export default {
    devtool: 'cheap-eval-source-map',

    target: 'node',

    module: {
        rules: [
            {
                test: /\.tsx?$/,
                exclude: /node_modules/,
                use: ['babel-loader', 'ts-loader'],
            }, {
                test: /\.scss$/,
                use: 'ignore-loader',
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

    node: {
        console: true,
        fs: 'empty',
        net: 'empty',
        tls: 'empty',
    },

    externals: {
        'react/lib/ExecutionEnvironment': true,
        'react/lib/ReactContext': true,
        'react/addons': true,
    },
};

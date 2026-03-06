const path = require('path');

module.exports = {
    entry: {
        whiteboard: './whiteboard.js',
        puzzle: './puzzle/index.js',
        memory_game: './memory_game/index.js',
        my_games: './my-games.js'
    },
    output: {
        path: path.resolve(__dirname, '../static/js/game/'),
        filename: '[name].bundle.js',
        clean: true,
    },
    module: {
        rules: [{
            test: /\.js$/,
            exclude: /node_modules/,
            use: {
                loader: 'babel-loader',
                options: { presets: ['@babel/preset-env'] }
            }
        }]
    },
    mode: 'development',
};
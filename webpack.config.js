const path = require('path');

module.exports = {
  entry: {
    'core': './src/index.js',
  },
  output: {
    filename: '[name]_v1.bundle.js',
    path: path.resolve(__dirname, 'static/js'),

  },
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['@babel/preset-env'],
          }
        }
      },
    ]
  }
};
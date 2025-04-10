const path = require('path');

module.exports = {
  entry: './frontend/src/ts/app.ts',
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: 'ts-loader',
        exclude: /node_modules/,
      },
    ],
  },
  resolve: {
    extensions: ['.tsx', '.ts', '.js'],
    alias: {
      '@': path.resolve(__dirname, 'frontend/src/ts'),
      '@modules': path.resolve(__dirname, 'frontend/src/ts/modules'),
      '@utils': path.resolve(__dirname, 'frontend/src/ts/utils'),
      '@types': path.resolve(__dirname, 'frontend/src/ts/types'),
    },
  },
  output: {
    filename: 'app.js',
    path: path.resolve(__dirname, 'frontend/static/js'),
  },
  devtool: 'source-map',
}; 
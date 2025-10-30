const path = require("path");

module.exports = {
  entry: {
    core: "./src/index.js",
  },
  output: {
    filename: "[name]_v52.bundle.js",
    path: path.resolve(__dirname, "static/js"),
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: {
          loader: "babel-loader",
          options: {
            presets: ["@babel/preset-env"],
          },
        },
      },
      {
        test: /\.scss$/,
        use: [
          "style-loader", // Inject styles into DOM
          "css-loader", // Translates CSS into CommonJS
          "sass-loader", // Compiles SCSS to CSS
        ],
      },
    ],
  },
};

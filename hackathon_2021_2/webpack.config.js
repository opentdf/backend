
const path = require("path");


module.exports = {
  entry: "./src/index.js",
  mode: "development",
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /[\/\\]node_modules[\/\\]/,
        loader: "babel-loader",
        options: {
          presets: ["@babel/env"],
        },
      },
    ]
  },
  resolve: {
    extensions: ["*", ".js"],
  },
  output: {
    filename: "bundle.js",
    path: path.resolve(__dirname, "build/"),
    publicPath: "/static/",
  },
  devServer: {
    hot: true,
    port: 3000,
    static: path.join(__dirname, "static/"),
  },
  plugins: [],
};

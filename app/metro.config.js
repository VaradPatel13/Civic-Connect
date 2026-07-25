const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);

module.exports = {
  ...config,
  resolver: {
    ...config.resolver,
    // Register @src as an alias to ./src for module resolution
    alias: {
      ...(config.resolver.alias ?? {}),
      '^@src/(.*)$': './src/$1',
    },
    sourceExts: ['js', 'jsx', 'ts', 'tsx', 'json', 'cjs', 'mjs'],
    blockList: [
      /.*\/\.git\/.*/,
      /.*\/\.expo\/.*/,
    ],
  },
};
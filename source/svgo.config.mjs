export default {
  multipass: true,
  floatPrecision: 1,
  js2svg: { pretty: false },
  plugins: [
    "preset-default",
    "removeDimensions",
    { name: "mergePaths", params: { collapseRepeated: true, force: true } },
    { name: "cleanupNumericValues", params: { floatPrecision: 1 } },
    "removeElementsByAttr",
    "removeEmptyContainers",
    "removeHiddenElems",
    "removeUnusedNS",
    "sortAttrs",
    "removeStyleElement",
    "removeScripts",
    "removeTitle",
    { name: "removeAttrs", params: { attrs: ["svg:width", "svg:height", "data-name"] } }
  ]
};

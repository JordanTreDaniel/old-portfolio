export default {
  multipass: true,
  floatPrecision: 0,
  js2svg: { pretty: false },
  plugins: [
    "preset-default",
    "removeDimensions",
    { name: "mergePaths", params: { collapseRepeated: true, force: true } },
    { name: "cleanupNumericValues", params: { floatPrecision: 0 } },
    { name: "convertPathData", params: { floatPrecision: 0, transformPrecision: 0, shortSigns: true, utilizeAbsolute: false, leadingZero: false, makeArcs: { threshold: 2.5, tolerance: 8 } } },
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

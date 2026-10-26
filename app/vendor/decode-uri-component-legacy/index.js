'use strict';

// Metro and Node expose an ESM default through require differently. Both paths
// must reach the pinned upstream decoder; no old parser is kept as a fallback.
const upstream = require('decode-uri-component-modern');
const decode = typeof upstream === 'function' ? upstream : upstream.default;

module.exports = function decodeUriComponent(value) {
  // 0.2.x treated literal plus as a space. Query-string already does this;
  // source-map-resolve escapes a literal plus first. Preserve both callers.
  return decode(typeof value === 'string' ? value.replace(/\+/g, ' ') : value);
};

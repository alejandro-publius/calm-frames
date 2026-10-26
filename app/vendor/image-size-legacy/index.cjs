'use strict';

// No image parsers are copied here. Every parse uses the pinned upstream fix.
const fs = require('node:fs');
const path = require('node:path');
const { Buffer } = require('node:buffer');
const { imageSize, types } = require('image-size-modern');
const { imageSizeFromFile } = require('image-size-modern/fromFile');
const MAX_HEADER_BYTES = 512 * 1024;

function legacyImageSize(input, callback) {
  if (Buffer.isBuffer(input)) return imageSize(input);
  if (typeof input !== 'string') throw new TypeError('invalid invocation');
  const file = path.resolve(input);
  if (typeof callback === 'function') {
    imageSizeFromFile(file).then(
      (dimensions) => callback(null, dimensions),
      (error) => callback(error)
    );
    return undefined;
  }

  const descriptor = fs.openSync(file, 'r');
  try {
    const stats = fs.fstatSync(descriptor);
    if (!stats.isFile()) throw new TypeError('image input must be a regular file');
    if (stats.size <= 0) throw new TypeError('Empty file');
    const header = Buffer.alloc(Math.min(stats.size, MAX_HEADER_BYTES));
    let offset = 0;
    while (offset < header.length) {
      const read = fs.readSync(descriptor, header, offset, header.length - offset, offset);
      if (read === 0) break;
      offset += read;
    }
    return imageSize(header.subarray(0, offset));
  } finally {
    fs.closeSync(descriptor);
  }
}

legacyImageSize.types = [...types];
module.exports = legacyImageSize;

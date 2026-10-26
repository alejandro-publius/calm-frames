# Legacy URI decoder adapter

The existing query-string 7.1.3 and source-map-resolve 0.5.3 consumers expect a
CommonJS callable. decode-uri-component 0.5.1 fixes GHSA-vcc3-ghjq-m6fr with a
bounded scan, but exports an ES-module default. This adapter unwraps that export
and preserves the old literal-plus convention. It does not copy, backport or
fall back to the vulnerable decoder. The exact upstream version is pinned in
the app manifest and lock, and is included in the generated SBOM.

Ordinary URLs, malformed UTF-8, arrays, source-map data and navigation parsing
are checked through the installed consumers. Some deliberately malformed
sequences differ from 0.2.2: upstream no longer repeatedly decodes text that has
already been decoded. Those differences are retained as part of the fix.
Native package resolution still needs a new exact-build inventory; old native
inventories describe the old dependency graph.

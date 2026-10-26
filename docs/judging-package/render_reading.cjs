// Optional authoring tool. The generated pages need no packages at runtime.
// Uses the environment's marked package; does not install or fetch anything.
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const crypto = require('node:crypto');

const root = path.resolve(__dirname, '../..');
const documents = new Map([
  ['docs/judging-package/ARCHITECTURE.md', 'architecture.html'],
  ['docs/judging-package/CLAIMS_LEDGER.md', 'claims-ledger.html'],
  ['docs/judging-package/DEMO_EVIDENCE_BRIEF.md', 'demo-evidence-brief.html'],
  ['docs/judging-package/FRICTION_LOG_DRAFT.md', 'friction-log-draft.html'],
  ['docs/judging-package/GUIDE.md', 'guide.html'],
  ['docs/judging-package/HANDOFF.md', 'handoff.html'],
  ['docs/judging-package/IMPACT_AND_DIFFERENTIATION.md', 'impact-and-differentiation.html'],
  ['docs/judging-package/PRESENTATION_DRAFTS.md', 'presentation-drafts.html'],
  ['docs/judging-package/PRIMARY_SOURCES.md', 'primary-sources.html'],
  ['docs/judging-package/PRODUCT_FEEDBACK_DRAFT.md', 'product-feedback-draft.html'],
  ['docs/judging-package/README.md', 'package-notes.html'],
  ['docs/judging-package/RUBRIC_MATRIX.md', 'rubric-matrix.html'],
  ['docs/judging-package/evidence/architecture-source.md', 'architecture-source.html'],
  ['docs/judging-package/evidence/capture-history.md', 'capture-history.html'],
  ['docs/judging-package/evidence/code-excerpts.md', 'code-excerpts.html'],
  ['docs/judging-package/evidence/friction-records.md', 'friction-records.html'],
  ['docs/judging-package/evidence/outreach-status.md', 'outreach-status.html'],
  ['docs/judging-package/evidence/preparation-recovery.md', 'preparation-recovery.html'],
  ['docs/judging-package/evidence/recorded-rules.md', 'recorded-rules.html'],
  ['docs/judging-package/evidence/release-readiness.md', 'release-readiness.html'],
  ['docs/judging-package/evidence/spec-sources.md', 'spec-sources.html'],
  ['docs/judging-package/validation/README.md', 'validation.html'],
]);
const out = path.join(__dirname, 'reading');
const escape = (text) => text.replaceAll('&', '&amp;').replaceAll('"', '&quot;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');

(async () => {
  const { Marked } = await import(pathToFileURL(require.resolve('marked')).href);
  fs.mkdirSync(out, { recursive: true });
  for (const [source, name] of documents) {
    const text = fs.readFileSync(path.join(root, source), 'utf8');
    const ids = new Map();
    const parser = new Marked({ gfm: true });
    parser.use({ renderer: {
      heading({ tokens, depth, text: heading }) {
        const base = heading.toLowerCase().replace(/<[^>]*>/g, '').replace(/[^\p{L}\p{N}_\s-]/gu, '').replace(/\s/g, '-');
        const count = ids.get(base) || 0;
        ids.set(base, count + 1);
        return `<h${depth} id="${escape(base + (count ? '-' + count : ''))}">${this.parser.parseInline(tokens)}</h${depth}>\n`;
      },
    } });
    let body = parser.parse(text);
    body = body.replace(/(href|src)="([^"\n]+)"/g, (all, attribute, value) => {
      if (/^(?:[a-z]+:|\/\/|#)/i.test(value)) return all;
      const [file, fragment] = value.split('#');
      const resolved = path.posix.normalize(path.posix.join(path.posix.dirname(source), file));
      const dest = documents.has(resolved)
        ? documents.get(resolved)
        : path.relative(out, path.join(root, resolved)).split(path.sep).join('/');
      return `${attribute}="${dest}${fragment ? '#' + fragment : ''}"`;
    });
    const title = text.match(/^# (.+)/m)[1];
    const original = path.relative(out, path.join(root, source)).split(path.sep).join('/');
    const hash = crypto.createHash('sha256').update(text).digest('hex');
    fs.writeFileSync(path.join(out, name), `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src 'self' data:; font-src 'self'; style-src 'self'; base-uri 'none'">
<title>${escape(title)} | Calm Frames</title><link rel="icon" href="../assets/icon.png" type="image/png"><link rel="stylesheet" href="../styles.css"><link rel="stylesheet" href="../reading.css"></head>
<body><a class="skip-link" href="#document">Skip to document</a><header class="site-header wrap"><a class="wordmark" href="../index.html">≈ Calm Frames</a><nav aria-label="Reading navigation"><a href="../index.html#evidence">Back to review</a><a href="${original}">Original Markdown</a></nav></header>
<main class="reading wrap" id="document"><p class="reading-note">Offline reading copy. Historical observations retain their original scope and date. Draft proposals are not published changes; this rendering is not a new validation run.</p>${body}</main>
<footer class="reading-footer wrap"><p>Source: <a href="${original}">${escape(source)}</a></p><p>Source SHA-256: <code>${hash}</code></p><a href="../index.html">Return to the guided review</a></footer></body></html>\n`);
  }
  // Keep the browser entry links pointed at the readable copies.
  const entry = path.join(__dirname, 'index.html');
  let html = fs.readFileSync(entry, 'utf8');
  html = html.replace(/href="([^"\n]+)"/g, (all, value) => {
    if (/^(?:[a-z]+:|\/\/|#)/i.test(value)) return all;
    const [file, fragment] = value.split('#');
    const resolved = path.posix.normalize(path.posix.join('docs/judging-package', file));
    if (!documents.has(resolved)) return all;
    return `href="reading/${documents.get(resolved)}${fragment ? '#' + fragment : ''}"`;
  });
  fs.writeFileSync(entry, html);
  console.log(`Rendered ${documents.size} source documents for offline reading.`);
})().catch((error) => { console.error(error); process.exitCode = 1; });

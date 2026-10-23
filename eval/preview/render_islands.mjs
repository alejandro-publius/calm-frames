// Render exported Home host trees in Chromium, explicitly not Vega.
//
// Run eval/preview/islands.fixture.tsx first (copied into app/test/calmframes),
// then: node eval/preview/render_islands.mjs [out-dir]
// The page uses the actual styles, text, images and map SVG. Browser flexbox
// stands in for Yoga, so this shows composition and overlap, not native pixels.
// Needs playwright-core on NODE_PATH and Chromium at CHROMIUM or the cloud
// container's /opt/pw-browsers path.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright-core');
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const TREES = path.join(ROOT, 'app/build/islands-preview');
const OUT = path.resolve(process.argv[2] ?? TREES);
const CHROMIUM = process.env.CHROMIUM ?? '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';

const escape = (text) => String(text).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
const flatten = (value) => Array.isArray(value) ? Object.assign({}, ...value.map(flatten)) : value && typeof value === 'object' ? value : {};
const kebab = (key) => key.replace(/[A-Z]/g, (m) => '-' + m.toLowerCase());
const UNITLESS = new Set(['flex', 'flexGrow', 'flexShrink', 'opacity', 'zIndex', 'fontWeight', 'order']);

function css(value) {
  const values = { ...flatten(value) };
  for (const prefix of ['padding', 'margin', 'border']) {
    for (const [direction, sides] of [['Horizontal', ['Left', 'Right']], ['Vertical', ['Top', 'Bottom']]]) {
      const key = prefix === 'border' ? undefined : prefix + direction;
      if (key && key in values) {
        const v = values[key];
        delete values[key];
        for (const side of sides) if (!(prefix + side in values)) values[prefix + side] = v;
      }
    }
  }
  // React Native resolves borderBottomWidth over borderWidth; CSS needs the sides spelled out.
  if ('borderWidth' in values) {
    for (const side of ['Top', 'Right', 'Bottom', 'Left']) if (!(`border${side}Width` in values)) values[`border${side}Width`] = values.borderWidth;
    delete values.borderWidth;
  }
  if ('borderColor' in values) {
    for (const side of ['Top', 'Right', 'Bottom', 'Left']) if (!(`border${side}Color` in values)) values[`border${side}Color`] = values.borderColor;
    delete values.borderColor;
  }
  if (values.flex === 1) Object.assign(values, { flex: '1 1 0%', minHeight: 0, minWidth: 0 });
  const out = [];
  for (const [key, raw] of Object.entries(values)) {
    if (raw === null || raw === undefined || ['elevation', 'shadowOffset', 'shadowColor', 'shadowRadius', 'shadowOpacity'].includes(key)) continue;
    let v = raw;
    if (key === 'transform') v = raw.map((t) => Object.entries(t).map(([k, n]) => `${k}(${n}${k.startsWith('translate') ? 'px' : ''})`).join(' ')).join(' ');
    else if (typeof raw === 'number' && !UNITLESS.has(key)) v = `${raw}px`;
    out.push(`${kebab(key)}:${v}`);
  }
  return out.join(';');
}

const SVG_TAGS = { Svg: 'svg', G: 'g', Path: 'path', Rect: 'rect', Ellipse: 'ellipse', Circle: 'circle' };
const SVG_SKIP = new Set(['children', 'testID', 'style']);
function svgAttributes(props) {
  return Object.entries(props).filter(([k, v]) => !SVG_SKIP.has(k) && v !== undefined && typeof v !== 'object')
    .map(([k, v]) => `${k === 'viewBox' || k === 'preserveAspectRatio' ? k : kebab(k)}="${escape(v)}"`).join(' ');
}

function image(source) {
  const one = Array.isArray(source) ? source[0] : source ?? {};
  const uri = one.testUri ?? '';
  if (!uri.includes('assets/')) throw new Error(`Unresolved preview image: ${JSON.stringify(one)}`);
  const file = path.join(ROOT, 'app/assets', uri.split('assets/')[1]);
  const mime = file.endsWith('.jpg') ? 'image/jpeg' : 'image/png';
  return `data:${mime};base64,${fs.readFileSync(file).toString('base64')}`;
}

function render(node) {
  if (node === null || node === undefined || node === false) return '';
  if (Array.isArray(node)) return node.map(render).join('');
  if (typeof node === 'string' || typeof node === 'number') return escape(node);
  const { type, props = {} } = node;
  const id = escape(props.testID ?? '');
  if (SVG_TAGS[type]) {
    const tag = SVG_TAGS[type];
    const ns = tag === 'svg' ? ` xmlns="http://www.w3.org/2000/svg" style="display:block;flex-shrink:0;${css(props.style)}"` : '';
    return `<${tag}${ns} data-testid="${id}" ${svgAttributes(props)}>${render(node.children)}</${tag}>`;
  }
  if (type === 'Image') {
    const fit = props.resizeMode === 'cover' ? 'cover' : 'contain';
    return `<img data-testid="${id}" style="${css(props.style)};object-fit:${fit}" src="${image(props.source)}">`;
  }
  let style = css(props.style);
  if (type === 'LinearGradient') {
    const { start = { x: 0, y: 0 }, end = { x: 0, y: 1 }, colors, locations } = props;
    const direction = start.x === end.x ? (end.y > start.y ? 'to bottom' : 'to top') : (end.x > start.x ? 'to right' : 'to left');
    const stops = locations ? colors.map((c, i) => `${c} ${locations[i] * 100}%`) : colors;
    style += `;background:linear-gradient(${direction},${stops.join(',')})`;
  }
  const tag = type === 'Text' ? 'span' : 'div';
  let cls = type === 'Text' ? 'text' : 'view';
  let children = node.children;
  if (type === 'RCTScrollView' || type === 'ScrollView') {
    cls += ' scroll';
    if (children?.length === 1 && typeof children[0] === 'object') {
      children = [{ ...children[0], props: { ...children[0].props, style: props.contentContainerStyle ?? {} } }];
    }
  }
  const role = props.accessibilityRole === 'button' || /-(watch|more-info|learn|parent-area|choose-profile)$|-poster-prepared-/.test(props.testID ?? '') ? ' role="button"' : '';
  return `<${tag} class="${cls}"${role} data-testid="${id}" style="${style}">${render(children)}</${tag}>`;
}

const fontData = (name) => `data:font/ttf;base64,${fs.readFileSync(path.join(ROOT, 'app/assets/fonts', name + '.ttf')).toString('base64')}`;
const fonts = ['CalmSansRegular', 'CalmSansSemibold', 'CalmDisplaySemibold'].map((name) => `@font-face{font-family:${name};src:url(${fontData(name)})}`).join('');
const PAGE_CSS = `*{box-sizing:border-box}html,body{margin:0;width:1920px;height:1080px;overflow:hidden}body{display:flex;flex-direction:column}
.view{display:flex;flex-direction:column;position:relative;flex-shrink:0;min-height:0;min-width:0;border-style:solid;border-width:0}
.text{display:block;position:relative;flex-shrink:0;white-space:pre-wrap;border-style:solid;border-width:0}img{display:block;flex-shrink:0;border-style:solid;border-width:0}.scroll{overflow:hidden}`;

fs.mkdirSync(OUT, { recursive: true });
const browser = await chromium.launch({ executablePath: CHROMIUM, args: ['--no-sandbox'] });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
const bounds = {};
for (const file of fs.readdirSync(TREES).filter((f) => f.endsWith('.json') && !f.startsWith('bounds')).sort()) {
  const name = file.replace(/\.json$/, '');
  const tree = JSON.parse(fs.readFileSync(path.join(TREES, file), 'utf8'));
  const html = `<!doctype html><html><head><meta charset="utf-8"><title>${name}: browser approximation, not Vega</title><style>${fonts}${PAGE_CSS}</style></head><body>${render(tree)}</body></html>`;
  fs.writeFileSync(path.join(TREES, name + '.html'), html);
  await page.setContent(html);
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: path.join(OUT, `${name}.png`) });
  bounds[name] = await page.$$eval('[data-testid]', (els) => els.filter((e) => e.dataset.testid).map((e) => {
    const r = e.getBoundingClientRect();
    return { id: e.dataset.testid, left: Math.round(r.left), top: Math.round(r.top), right: Math.round(r.right), bottom: Math.round(r.bottom) };
  }));
}
fs.writeFileSync(path.join(OUT, 'bounds.json'), JSON.stringify(bounds, null, 1) + '\n');
await browser.close();
console.log(OUT);

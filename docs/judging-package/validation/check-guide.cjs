// Bounded documentation validation. Requires existing Playwright and Chromium.
// It does not install dependencies, build the app, contact external sites or run benchmarks.
const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
fs.writeFileSync(path.join(__dirname,'checks.json'), JSON.stringify({status:'running',scope:'Guide validation in progress; not a passing receipt.'},null,2)+'\n');
const types = { '.html':'text/html', '.css':'text/css', '.js':'text/javascript', '.json':'application/json', '.png':'image/png', '.svg':'image/svg+xml', '.ttf':'font/ttf', '.md':'text/plain' };
const hash = (p) => crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const server = http.createServer((req, res) => {
  const location = new URL(req.url, 'http://localhost');
  const file = path.resolve(root, '.' + decodeURIComponent(location.pathname === '/' ? '/index.html' : location.pathname));
  if (!file.startsWith(root + path.sep) || !fs.existsSync(file) || !fs.statSync(file).isFile()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, {'Content-Type': types[path.extname(file)] || 'text/plain'});
  fs.createReadStream(file).pipe(res);
});

(async () => {
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const origin = 'http://127.0.0.1:' + server.address().port;
  const browser = await chromium.launch({ executablePath:process.env.CHROMIUM_PATH || '/usr/bin/chromium', headless:true, args:['--no-sandbox'] });
  try {
    const context = await browser.newContext({ viewport:{width:1440,height:1000} });
    const page = await context.newPage();
    const errors=[], remote=[];
    page.on('pageerror', e => errors.push(e.message));
    page.on('console', m => { if (m.type()==='error') errors.push(m.text()); });
    await context.route('**/*', route => {
      if (/^https?:/.test(route.request().url()) && !route.request().url().startsWith(origin + '/')) {
        remote.push(route.request().url()); return route.abort();
      }
      return route.continue();
    });
    await page.goto(origin + '/index.html');
    await page.evaluate(() => document.fonts.ready);
    assert.equal(await page.locator('video,audio,iframe').count(),0);
    assert.equal(await page.locator('[autoplay]').count(),0);
    const stops = page.locator('[data-stop]');
    for(let i=0;i<5;i++){
      await stops.nth(i).focus(); await page.keyboard.press('Enter');
      assert.equal(await stops.nth(i).getAttribute('aria-pressed'),'true');
      assert.equal(await page.locator('.tour-panel:visible').count(),1);
      await page.locator('.tour-panel:visible img').evaluate(img => img.decode());
    }
    await page.locator('[data-stop="0"]').focus(); await page.keyboard.press('Enter');
    assert.equal(await page.locator('#previous-stop').isDisabled(),true);
    await page.locator('#next-stop').focus(); await page.keyboard.press('Enter');
    assert.equal(await page.locator('#stop-playback').isVisible(),true);
    for (let i=0;i<3;i++) await page.keyboard.press('Enter');
    assert.equal(await page.locator('#next-stop').isDisabled(),true);
    assert.equal(await page.locator('#previous-stop').evaluate(el=>el===document.activeElement),true);
    for (let i=0;i<4;i++) await page.keyboard.press('Enter');
    assert.equal(await page.locator('#previous-stop').isDisabled(),true);
    assert.equal(await page.locator('#next-stop').evaluate(el=>el===document.activeElement),true);
    await page.locator('[data-stop="0"]').click();
    await page.keyboard.press('Tab'); await page.keyboard.press('Tab');
    assert.equal(await page.locator('[data-stop="2"]').evaluate(el=>el===document.activeElement),true);
    const focus = await page.locator('[data-stop="2"]').evaluate(el => {
      const s=getComputedStyle(el);return {style:s.outlineStyle,width:s.outlineWidth,color:s.outlineColor};
    });
    assert.equal(focus.style,'solid'); assert.ok(parseFloat(focus.width)>=3);
    await page.locator('#experience').scrollIntoViewIfNeeded();
    await page.screenshot({path:path.join(__dirname,'keyboard-focus.png')});
    await page.locator('h1').click(); await page.evaluate(() => scrollTo(0,0));
    await page.screenshot({path:path.join(__dirname,'desktop.png'),fullPage:true});
    const viewports=[];
    for(const width of [1440,768,390,320]){
      await page.setViewportSize({width,height:900});
      const overflow=await page.evaluate(() => document.documentElement.scrollWidth>innerWidth);
      assert.equal(overflow,false,'Horizontal overflow at '+width);
      viewports.push({width,horizontal_overflow:overflow});
    }
    await page.setViewportSize({width:390,height:900});
    await page.evaluate(()=>scrollTo(0,0));
    await page.screenshot({path:path.join(__dirname,'narrow-first-screen.png')});
    await page.screenshot({path:path.join(__dirname,'narrow.png'),fullPage:true});
    await page.emulateMedia({reducedMotion:'reduce'});
    const motion = await page.evaluate(() => ({ preference:matchMedia('(prefers-reduced-motion: reduce)').matches, animations:document.getAnimations().length, smooth:[...document.querySelectorAll('*')].some(e=>getComputedStyle(e).scrollBehavior==='smooth') }));
    assert.equal(motion.preference,true);assert.equal(motion.animations,0);assert.equal(motion.smooth,false);
    // Contrast for every visible text node on the authored main page. Excludes bitmap text.
    const measureContrast = () => {
      const rgb=s=>(s.match(/[\d.]+/g)||[]).map(Number);
      const blend=(a,b)=>{const alpha=a.length>3?a[3]:1;return [0,1,2].map(i=>a[i]*alpha+b[i]*(1-alpha));};
      const lum=c=>c.slice(0,3).map(x=>{x/=255;return x<=.04045?x/12.92:((x+.055)/1.055)**2.4;}).reduce((v,x,i)=>v+x*[.2126,.7152,.0722][i],0);
      const ratio=(a,b)=>{const l=[lum(a),lum(b)].sort((a,b)=>b-a);return (l[0]+.05)/(l[1]+.05);};
      const bg=e=>{const stack=[];for(let n=e;n;n=n.parentElement)stack.unshift(rgb(getComputedStyle(n).backgroundColor));return stack.reduce((v,c)=>blend(c,v),[255,255,255]);};
      const nodes=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT), failures=[];let min=100,count=0,n;
      while(n=nodes.nextNode()){
        if(!n.textContent.trim())continue;const e=n.parentElement;if(!e||!e.checkVisibility({checkVisibilityCSS:true})||e.closest('script,style'))continue;
        const range=document.createRange();range.selectNodeContents(n);if(!range.getBoundingClientRect().width)continue;
        const s=getComputedStyle(e),back=bg(e),r=ratio(blend(rgb(s.color),back),back),size=parseFloat(s.fontSize),bold=parseInt(s.fontWeight)>=700;
        const threshold=size>=24||(size>=18.66&&bold)?3:4.5;count++;min=Math.min(min,r);
        if(r+.01<threshold)failures.push({text:n.textContent.trim().slice(0,80),ratio:r,threshold});
      }
      const focusRatio=ratio([146,62,40],[247,243,232]);
      return {visible_text_nodes:count,minimum_ratio:Number(min.toFixed(2)),failures,focus_ring_on_paper:Number(focusRatio.toFixed(2)),scope:'Computed CSS text and focus colors; native screenshot pixels are historical evidence, not guide text.'};
    };
    const contrast = await page.evaluate(measureContrast);
    assert.deepEqual(contrast.failures,[]);assert.ok(contrast.focus_ring_on_paper>=3);
    const files=['index.html',...fs.readdirSync(path.join(root,'reading')).filter(n=>n.endsWith('.html')).map(n=>'reading/'+n)];
    let refs=0,images=0;const documentContrast=[];
    for(const file of files){
      await page.goto(origin+'/'+file);await page.evaluate(()=>document.fonts.ready);
      await page.locator('img').evaluateAll(async imgs=>{for(const img of imgs){img.loading='eager';await img.decode();}});
      images+=await page.locator('img').count();
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'Reading-page overflow: '+file);
      const measured=await page.evaluate(measureContrast);
      assert.deepEqual(measured.failures,[],'Text contrast: '+file);
      documentContrast.push({file,visible_text_nodes:measured.visible_text_nodes,minimum_ratio:measured.minimum_ratio});
      const links=await page.locator('[href],[src]').evaluateAll(els=>els.map(e=>e.getAttribute('href')||e.getAttribute('src')));
      for(const ref of links){
        if(!ref||/^(?:https?:|mailto:|data:)/.test(ref))continue;
        const url=new URL(ref,origin+'/'+file), target=path.resolve(root,'.'+decodeURIComponent(url.pathname));
        assert.ok(target.startsWith(root+path.sep),'Escaped package: '+ref);
        assert.ok(fs.existsSync(target),'Missing '+ref+' in '+file);
        if(target.endsWith('.html')&&url.hash){assert.ok(fs.readFileSync(target,'utf8').includes('id="'+decodeURIComponent(url.hash.slice(1))+'"'),'Missing anchor '+ref+' in '+file);}
        refs++;
      }
    }
    const fallback=await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:900}});
    const plain=await fallback.newPage();await plain.goto(origin+'/index.html');
    assert.equal(await plain.locator('.tour-panel:visible').count(),5);assert.equal(await plain.locator('.tour-controls:visible').count(),0);
    assert.equal(await plain.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
    assert.deepEqual(errors,[]);assert.deepEqual(remote,[]);
    const assets=JSON.parse(fs.readFileSync(path.join(root,'assets.json'))).assets;
    for(const asset of assets){assert.equal(hash(path.join(root,asset.path)),asset.sha256);assert.equal(fs.statSync(path.join(root,asset.path)).size,asset.bytes);}
    const result={status:'passed',scope:'Judging-package browser guide only. No app build, native test, benchmark or external-source verification.',base_commit:'13551e45bd853c392489dbecce7158a04036f615',reused_page_commit:'3db0505f02441300020a8d6f023c94994be2ae88',browser:await browser.version(),keyboard_stops:5,no_javascript_stops:5,visible_focus:focus,contrast,reduced_motion:motion,viewports,html_documents:files.length,local_references:refs,decoded_images:images,verified_assets:assets.length,remote_requests:remote,browser_errors:errors,render_kind:'Web-guide screenshots, not native app captures.',file_opening:'Managed browser file-URL policy blocks direct navigation. Served the package alone on loopback for checks; no network-dependent runtime, fetch or module loading.',limitations:['Not a full WCAG audit or native accessibility acceptance.','Historical screenshot text is not audited as the authored guide interface.','Optional external source links were not verified by these local-link checks.']};
    result.document_contrast=documentContrast;
    fs.writeFileSync(path.join(__dirname,'checks.json'),JSON.stringify(result,null,2)+'\n');
    console.log(JSON.stringify(result));
  } finally { await browser.close(); server.close(); }
})().catch(e=>{fs.writeFileSync(path.join(__dirname,'checks.json'),JSON.stringify({status:'failed',scope:'Guide validation only',error:e.message},null,2)+'\n');console.error(e);server.close();process.exit(1);});

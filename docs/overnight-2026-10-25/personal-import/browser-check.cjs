/* Checks the local caregiver page, not native Fire TV rendering.
 * Usage: node browser-check.cjs URL OUTPUT_DIR GENERATED_FIXTURE_MP4
 * Requires an existing analyzed, fictional job and Playwright/Chromium.
 */
const {chromium} = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

async function main() {
  const [origin, output, fixture] = process.argv.slice(2);
  assert(origin && output && fixture, 'Provide URL, output directory and generated fixture.');
  assert.equal(new URL(origin).hostname, '127.0.0.1', 'Use the local intake only.');
  fs.mkdirSync(output, {recursive: true});
  const browser = await chromium.launch({executablePath: '/usr/bin/chromium', headless: true, args: ['--no-sandbox']});
  const context = await browser.newContext({viewport: {width: 1100, height: 1000}, reducedMotion: 'reduce', acceptDownloads: true});
  const page = await context.newPage();
  const errors = [], external = [], views = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('request', request => {
    if (/^https?:/.test(request.url()) && !request.url().startsWith(origin + '/')) external.push(request.url());
  });
  try {
    await page.goto(origin);
    await page.getByRole('button', {name: 'Save caregiver review (JSON)'}).waitFor();
    await page.getByLabel('Video title').fill('Generated fixture only');
    await page.getByLabel('Choose your video').setInputFiles(fixture);
    assert.equal(await page.locator('#upload').evaluate(form => form.checkValidity()), false);
    await page.getByRole('checkbox').check();
    assert.equal(await page.locator('#upload').evaluate(form => form.checkValidity()), true);
    await page.getByRole('checkbox').uncheck();

    const downloadControl = page.getByRole('button', {name: 'Save caregiver review (JSON)'});
    await page.getByLabel('Video title').focus();
    const keyboard = [];
    for (let i = 0; i < 18; i++) {
      await page.keyboard.press('Tab');
      const target = await page.evaluate(() => ({tag: document.activeElement.tagName, name: document.activeElement.textContent || document.activeElement.id}));
      keyboard.push(target);
      if (target.name === 'Save caregiver review (JSON)') break;
    }
    assert(keyboard.some(item => item.name === 'Save caregiver review (JSON)'), 'Review download reachable with Tab');
    assert.equal(await downloadControl.evaluate(button => getComputedStyle(button).outlineWidth), '3px');
    const downloadEvent = page.waitForEvent('download');
    await page.keyboard.press('Enter');
    const download = await downloadEvent;
    await download.saveAs(path.join(output, 'caregiver-review.json'));
    const report = JSON.parse(fs.readFileSync(path.join(output, 'caregiver-review.json'), 'utf8'));
    assert.equal(report.schema, 'calm-frames-caregiver-review-v1');
    assert.equal(report.analysis.analysis_complete, true);
    assert.equal(report.permission_verified_by_application, false);
    assert.equal(report.tv_playback_authorized, false);
    assert.equal(await page.locator('video,audio,iframe').count(), 0);
    assert.equal(await page.evaluate(() => document.getAnimations().length), 0);
    const contrast = await page.evaluate(() => {
      const luminance = color => {
        const channels = color.match(/[\d.]+/g).slice(0, 3).map(n => {
          const v = Number(n) / 255;
          return v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4;
        });
        return channels[0] * .2126 + channels[1] * .7152 + channels[2] * .0722;
      };
      const ratio = (a, b) => (Math.max(luminance(a), luminance(b)) + .05) / (Math.min(luminance(a), luminance(b)) + .05);
      const text = getComputedStyle(document.querySelector('p'));
      const root = getComputedStyle(document.documentElement);
      const button = getComputedStyle(document.querySelector('button[data-control="Save caregiver review (JSON)"]'));
      return {body: ratio(text.color, root.backgroundColor), review_button: ratio(button.color, button.backgroundColor), focus_ring: ratio(button.outlineColor, button.backgroundColor)};
    });
    assert(contrast.body >= 4.5 && contrast.review_button >= 4.5 && contrast.focus_ring >= 3);

    for (const viewport of [{width: 1100, height: 1000}, {width: 390, height: 844}]) {
      await page.setViewportSize(viewport);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, 'No horizontal overflow');
      const image = `${viewport.width === 1100 ? 'desktop' : 'narrow'}.png`;
      await page.screenshot({path: path.join(output, image), fullPage: true});
      views.push({...viewport, image, horizontal_overflow: false});
    }
    await context.setOffline(true);
    await page.waitForFunction(() => document.getElementById('notice').textContent.includes('Local connection lost'));
    await context.setOffline(false);
    await page.waitForFunction(() => document.getElementById('notice').textContent.includes('Local connection restored'), undefined, {timeout: 6000});
    assert.deepEqual(errors, []);
    assert.deepEqual(external, []);
    fs.writeFileSync(path.join(output, 'browser-checks.json'), JSON.stringify({
      native: false, scope: 'Local caregiver page using a generated steady-color fixture; no media playback.',
      views, keyboard_download: true, visible_focus: true, reduced_motion_requested: true,
      active_animations: 0, contrast,
      connection_loss_and_recovery: true, downloadable_review_verified: true,
      permission_required: true, external_requests: external, page_errors: errors,
    }, null, 2) + '\n');
  } finally { await browser.close(); }
}
main().catch(error => { console.error(error); process.exitCode = 1; });

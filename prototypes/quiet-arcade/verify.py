"""Drive the quiet arcade in headless Chromium and record what it did.

Serves the repository root, loads the prototype, presses the keys a remote
would press, clicks what a pointer would click, asserts the scene's own state
after each step, saves screenshots and a video, and writes verify.json.
Software rendering only: it says nothing about a television.
"""
import json
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / 'captures'
CHROME = ('/Users/alexvintera/Library/Caches/ms-playwright/chromium_headless_shell-1243/'
          'chrome-headless-shell-mac-arm64/chrome-headless-shell')
HOME = [3.9, 2.55, 5.5]


def free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def distance(current):
    return sum((a - b) ** 2 for a, b in zip(current['camera'], HOME)) ** 0.5


def drive(page, results):
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
    state = lambda: page.evaluate('window.__quietArcade.state()')
    menu = lambda: page.evaluate('({open: window.__quietArcadeMenu.isOpen(), name: window.__quietArcadeMenu.panelName()})')
    status = lambda: page.locator('#status').inner_text()
    active = lambda: page.evaluate('document.activeElement.id')

    def step(name, ok, detail=None):
        results['steps'].append({'step': name, 'ok': bool(ok), 'detail': detail})
        if not ok:
            raise AssertionError(f'{name}: {detail}')

    def settled(ms, predicate):
        # Software rendering can take hundreds of milliseconds a frame, so
        # every response is judged once the scene says it has finished.
        deadline = time.time() + ms / 1000
        while time.time() < deadline:
            current = state()
            if predicate(current):
                return current
            page.wait_for_timeout(60)
        return state()

    assert not page.evaluate('window.__quietArcade.fallback'), 'fell back'
    page.wait_for_timeout(400)
    page.screenshot(path=str(OUT / '01-arcade.png'))
    step('renders the scene', state()['frames'] >= 1, state()['frames'])

    # Keyboard: into the stage, along the hotspots, greet the keeper.
    page.focus('#stage')
    step('focusing the stage focuses the first hotspot', state()['focused'] == 'keeper', status())
    page.keyboard.press('ArrowRight')
    step('Right moves focus to the Harbor cabinet', state()['focused'] == 'harbor', status())
    page.keyboard.press('ArrowRight')
    page.keyboard.press('ArrowRight')
    step('Right wraps back to the keeper', state()['focused'] == 'keeper', status())
    page.keyboard.press('Enter')
    first = state()
    page.wait_for_timeout(350)
    page.screenshot(path=str(OUT / '02-keeper-greets.png'))
    done = settled(4000, lambda c: c['responseDone'])
    peak = done['responsePeak']
    step('Enter greets: the keeper bows while the lantern brightens, then rests',
         first['selected'] == 'keeper' and first['lastResponse'] == 'bow' and done['responseDone']
         and peak['bow'] > 0.15 and peak['lantern'] > 4.0 and abs(done['bow']) < 0.01 and abs(done['lantern'] - 2.2) < 0.05,
         {'peak': peak, 'rest_bow': done['bow'], 'rest_lantern': done['lantern']})
    page.keyboard.press('Escape')
    step('Escape clears the selection', state()['selected'] is None, status())

    # Selecting a cabinet eases the camera a little; Escape brings it home.
    page.keyboard.press('ArrowRight')
    page.keyboard.press('Enter')
    settled(3000, lambda c: distance(c) > 0.1)
    page.wait_for_timeout(900)
    moved = state()
    step('selecting the Harbor cabinet eases the camera a small distance',
         moved['selected'] == 'harbor' and 0.1 < distance(moved) < 0.6, {'drift': distance(moved)})
    page.screenshot(path=str(OUT / '03-harbor-selected.png'))
    page.keyboard.press('Escape')
    back = settled(3000, lambda c: distance(c) < 0.01)
    step('Escape returns the camera home', distance(back) < 0.01, back['camera'])

    # Up reaches the menu; Atmosphere lists plainly labelled choices.
    page.keyboard.press('ArrowUp')
    step('Up moves focus to the menu', active() == 'try-demo', active())
    page.keyboard.press('ArrowRight')
    page.keyboard.press('Enter')
    step('Atmosphere opens its panel', menu() == {'open': True, 'name': 'atmosphere'}, menu())
    labels = page.locator('#panel li button').all_inner_texts()
    step('Forest and Coast say they are not built',
         any('Forest' in l and 'Not built yet' in l for l in labels) and any('Coast' in l and 'Not built yet' in l for l in labels), labels)
    page.screenshot(path=str(OUT / '04-atmosphere.png'))
    page.keyboard.press('ArrowDown')
    page.keyboard.press('Enter')
    step('choosing Forest only says it is not built', menu()['open'] and 'Forest is not built yet' in status(), status())
    page.keyboard.press('Escape')
    step('Escape closes the panel and returns focus to Atmosphere', not menu()['open'] and active() == 'atmosphere', active())

    # Try demo is a prototype interaction and says so.
    page.click('#try-demo')
    step('Try demo says the real demo is not wired here',
         menu()['name'] == 'try-demo' and 'not wired' in page.locator('#panel-body').inner_text() and state()['demoLit'],
         page.locator('#panel-body').inner_text())
    page.wait_for_timeout(400)
    page.screenshot(path=str(OUT / '05-try-demo.png'))
    page.keyboard.press('Escape')
    step('closing Try demo dims the demo cabinet again', not state()['demoLit'], state()['demoLit'])

    # Help lists the keys.
    page.click('#help')
    step('Help lists the keys', menu()['name'] == 'help' and 'Escape' in page.locator('#panel-body').inner_text(), None)
    page.screenshot(path=str(OUT / '06-help.png'))
    page.keyboard.press('Escape')

    # Still: no transform animates; the greeting is light only.
    page.click('#still')
    step('Still turns on', state()['still'] and page.get_attribute('#still', 'aria-pressed') == 'true', None)
    page.focus('#stage')
    page.evaluate("window.__quietArcade.focus('keeper')")
    page.keyboard.press('Enter')
    first = state()
    done = settled(4000, lambda c: c['responseDone'])
    peak = done['responsePeak']
    step('in Still mode the keeper does not move, only the lantern answers',
         first['lastResponse'] == 'glow' and abs(peak['bow']) < 1e-6 and peak['lantern'] > 4.0 and abs(done['lantern'] - 2.2) < 0.05, peak)
    page.keyboard.press('Escape')
    page.evaluate("window.__quietArcade.focus('demo')")
    page.keyboard.press('Enter')
    page.wait_for_timeout(100)
    step('in Still mode a cabinet selection does not animate the camera', state()['selected'] == 'demo', state()['camera'])
    page.keyboard.press('Escape')
    page.click('#still')
    step('Still turns off again', not state()['still'], None)

    # Pointer: click the demo cabinet where it is drawn, then the empty floor.
    pos = page.evaluate("window.__quietArcade.screenPosition('demo')")
    page.mouse.click(pos['x'], pos['y'])
    page.wait_for_timeout(100)
    step('clicking the demo cabinet selects it', state()['selected'] == 'demo', pos)
    settled(3000, lambda c: distance(c) > 0.1)
    page.wait_for_timeout(900)
    page.screenshot(path=str(OUT / '07-demo-pointer.png'))
    empty = page.evaluate('window.__quietArcade.pickAt(120, 980)')
    page.mouse.click(120, 980)
    page.wait_for_timeout(100)
    step('clicking empty floor clears it', empty is None and state()['selected'] is None, empty)

    step('no page errors', not errors, errors)
    results['frames'] = state()['frames']


def drive_fallback(page, results):
    def step(name, ok, detail=None):
        results['steps'].append({'step': name, 'ok': bool(ok), 'detail': detail})
        if not ok:
            raise AssertionError(f'{name}: {detail}')
    page.wait_for_timeout(300)
    step('forced fallback shows the still and keeps the menu',
         page.evaluate('window.__quietArcade.fallback') and page.locator('#fallback').is_visible() and page.locator('#stage').is_hidden(), None)
    page.click('#atmosphere')
    step('the menu works in the fallback', page.evaluate('window.__quietArcadeMenu.isOpen()'), None)
    page.screenshot(path=str(OUT / '08-fallback.png'))


def main():
    OUT.mkdir(exist_ok=True)
    shutil.rmtree(OUT / 'video', ignore_errors=True)
    port = free_port()
    server = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'],
                              cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f'http://127.0.0.1:{port}/prototypes/quiet-arcade/'
    results = {'url': url, 'steps': []}
    video_path = None
    try:
        time.sleep(0.6)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, executable_path=CHROME,
                                        args=['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
            context = browser.new_context(viewport={'width': 1920, 'height': 1080}, record_video_dir=str(OUT / 'video'),
                                          record_video_size={'width': 1920, 'height': 1080})
            page = context.new_page()
            try:
                page.goto(url)
                page.wait_for_function('window.__quietArcade && window.__quietArcade.ready', timeout=20000)
                drive(page, results)
            except AssertionError as error:
                results['failure'] = str(error)
            video_path = page.video.path() if page.video else None
            context.close()
            browser.close()
            if 'failure' not in results:
                browser = p.chromium.launch(headless=True, executable_path=CHROME)
                page = browser.new_page(viewport={'width': 1920, 'height': 1080})
                try:
                    page.goto(url + '?fallback=1')
                    page.wait_for_function('window.__quietArcade && window.__quietArcade.ready', timeout=20000)
                    drive_fallback(page, results)
                except AssertionError as error:
                    results['failure'] = str(error)
                browser.close()
    finally:
        server.terminate()
    if video_path and Path(video_path).exists():
        target = OUT / 'interaction.webm'
        shutil.move(video_path, target)
        shutil.rmtree(OUT / 'video', ignore_errors=True)
        results['video'] = str(target.relative_to(HERE))
    if (OUT / '01-arcade.png').exists():
        shutil.copy(OUT / '01-arcade.png', OUT / 'fallback.png')
    results['renderer'] = 'headless Chromium with SwiftShader, 1920 by 1080'
    results['all_ok'] = all(s['ok'] for s in results['steps']) and 'failure' not in results
    (OUT / 'verify.json').write_text(json.dumps(results, indent=2) + '\n')
    print(json.dumps({'steps': len(results['steps']), 'all_ok': results['all_ok'], 'failure': results.get('failure')}))
    sys.exit(0 if results['all_ok'] else 1)


if __name__ == '__main__':
    main()

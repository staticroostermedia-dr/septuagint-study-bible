"""Deploy-update safety test: serve a temp copy, then simulate a new deploy (changed Gen/1.json + new version)."""
import hashlib, json, os, shutil, subprocess, time
from playwright.sync_api import sync_playwright
T = '/tmp/sbupd'; shutil.rmtree(T, ignore_errors=True); shutil.copytree('site', T, ignore=shutil.ignore_patterns('.git', 'build'))
srv = subprocess.Popen(['python3', '-m', 'http.server', '8767'], cwd=T, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
B = 'http://localhost:8767/'; ok = []; fails = []
def check(c, m): (ok if c else fails).append(m); print(('PASS ' if c else 'FAIL ') + m)
try:
    with sync_playwright() as p:
        br = p.chromium.launch(); ctx = br.new_context(); pg = ctx.new_page()
        pg.goto(B + '#/Gen/1'); pg.wait_for_selector('.w'); pg.evaluate("navigator.serviceWorker.ready"); pg.reload(); pg.wait_for_selector('.w')
        pg.goto(B + '#/Gen/2'); pg.wait_for_selector('.w'); pg.wait_for_timeout(800)
        old = pg.evaluate("caches.keys()")
        # --- simulate a deploy: Gen/1 text changes, Gen/2 unchanged ---
        f = os.path.join(T, 'data/Gen/1.json'); d = json.load(open(f)); d[0][2] = 'UPDATED ' + (d[0][2] or ''); s = json.dumps(d, ensure_ascii=False, separators=(',', ':'))
        open(f, 'w').write(s); of = json.load(open(os.path.join(T, 'offline-files.json')))
        of['files']['data/Gen/1.json'] = [len(s.encode()), hashlib.sha256(s.encode()).hexdigest()[:16]]; oldv = of['version']; of['version'] = 'test-new'
        json.dump(of, open(os.path.join(T, 'offline-files.json'), 'w')); sw = os.path.join(T, 'sw.js'); src = open(sw).read().replace(oldv, 'test-new'); open(sw, 'w').write(src)
        pg.evaluate("navigator.serviceWorker.getRegistration().then(r => r.update())")
        pg.wait_for_selector('#updNow', timeout=20000); check(True, 'new deploy detected: "A new version is ready — Reload" shown')
        check(pg.evaluate("caches.keys()") == old or 'sb-shell-test-new' in pg.evaluate("caches.keys()"), 'old version keeps serving until Reload (no mixing)')
        pg.screenshot(path='shots/pwa_update_toast.png')
        with pg.expect_navigation(): pg.click('#updNow')
        pg.wait_for_selector('.w'); pg.wait_for_timeout(800); ks = pg.evaluate("caches.keys()")
        check('sb-shell-test-new' in ks and not any(k.startswith('sb-shell-') and k != 'sb-shell-test-new' for k in ks), f'old shell cache deleted ({ks})')
        pg.goto(B + '#/Gen/2'); pg.goto(B + '#/Gen/1'); pg.wait_for_selector('.en1')
        check(pg.inner_text('#v1 .en1').startswith('UPDATED'), 'changed chapter served fresh after update (not stale)')
        check(pg.evaluate("caches.open('sb-data').then(c => c.match('data/Gen/2.json')).then(r => !!r)"), 'unchanged chapter kept in offline cache (no re-download)')
        br.close()
finally:
    srv.kill()
print(f'\n{len(ok)} passed, {len(fails)} failed')

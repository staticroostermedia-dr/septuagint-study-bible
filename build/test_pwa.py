"""PWA tests. Usage: python3 test_pwa.py [base_url]   (default http://localhost:8766/)"""
import io, json, sys, urllib.request
from playwright.sync_api import sync_playwright
from PIL import Image
B = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8766/'
S = 'shots/'; ok, fails = [], []
def check(c, m): (ok if c else fails).append(m); print(('PASS ' if c else 'FAIL ') + m)
get = lambda u: urllib.request.urlopen(B + u).read()

m = json.loads(get('manifest.webmanifest'))
check(m['name'] == 'Septuagint Study Bible' and m['short_name'] and m['display'] == 'standalone', 'manifest: name/short_name/display')
check(m['start_url'] == './' and m['scope'] == './', 'manifest: relative start_url/scope')
sizes = {(i['sizes'], i.get('purpose', 'any')) for i in m['icons']}
check({('192x192', 'any'), ('512x512', 'any'), ('192x192', 'maskable'), ('512x512', 'maskable')} <= sizes, 'manifest: 192/512 + maskable icons')
for i in m['icons']:
    im = Image.open(io.BytesIO(get(i['src']))); check(f'{im.size[0]}x{im.size[1]}' == i['sizes'] and im.format == 'PNG', f'icon {i["src"]} is a {i["sizes"]} PNG')
of = json.loads(get('offline-files.json')); sw = get('sw.js').decode()
check(of['version'] in sw, f'sw.js cache version matches offline-files.json ({of["version"]}, {len(of["files"])} files, {of["total"]/1e6:.1f} MB)')

with sync_playwright() as p:
    br = p.chromium.launch()
    ctx = br.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2)
    errs = []; pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(B + '#/Gen/1'); pg.wait_for_selector('.w')
    check(pg.evaluate("navigator.serviceWorker.ready.then(r => !!r.active)"), 'service worker registers and activates')
    scope = pg.evaluate("navigator.serviceWorker.ready.then(r => r.scope)"); check(scope == B, f'SW scope is the site path ({scope})')
    cdp = ctx.new_cdp_session(pg); ie = cdp.send('Page.getInstallabilityErrors')['installabilityErrors']
    check(not ie, f'Chrome installability: no errors ({ie})')
    pg.reload(); pg.wait_for_selector('.w')
    check(pg.evaluate("!!navigator.serviceWorker.controller"), 'page is controlled by the SW after reload')
    names = pg.evaluate("caches.keys()"); check('sb-shell-' + of['version'] in names, f'shell cache is versioned ({names})')
    pg.locator('.w', has_text='ἐποίησεν').first.click(); pg.wait_for_selector('#panel:not([hidden]) .sum')
    pg.click('#more >> xpath=..', timeout=2000) if False else None
    g_on = pg.inner_text('#panel'); pg.wait_for_timeout(1500)          # let per-word data be cached
    pg.goto(B + '#/DanTh/7'); pg.wait_for_selector('.verpick'); pg.wait_for_timeout(500)
    ctx.set_offline(True)
    pg.goto(B + '#/Gen/1'); pg.reload(); pg.wait_for_selector('.w', timeout=10000)
    check(pg.locator('.verse').count() > 20 and pg.locator('.en1').count() > 0, 'offline: previously visited chapter (Gen 1) loads after reload, with English')
    pg.locator('.w', has_text='ἐποίησεν').first.click(); pg.wait_for_selector('#panel:not([hidden]) .sum', timeout=10000)
    pg.wait_for_timeout(800); import unicodedata; t = unicodedata.normalize('NFC', pg.inner_text('#panel')); check('ποιέω' in t and 'aorist' in t.lower(), 'offline: word card works (ποιέω, parse) ' + repr(t[:80]))
    pg.screenshot(path=S + 'pwa_offline_gen1_card.png')
    pg.goto(B + '#/DanTh/7'); pg.wait_for_selector('.verpick', timeout=10000); check('υἱὸς ἀνθρώπου' in pg.inner_text('#v13'), 'offline: Daniel 7 (visited) loads')
    pg.goto(B + '#/Isa/40'); pg.wait_for_timeout(1500); check(pg.locator('.verse').count() == 0, 'offline: unvisited chapter is not available before full download (expected)')
    ctx.set_offline(False)
    pg.goto(B + '#/Gen/1'); pg.wait_for_selector('.w'); pg.click('#menuBtn'); pg.wait_for_selector('#offline:not([hidden])')
    pg.wait_for_function("document.querySelector('#offStat').textContent.indexOf('Saved for offline') >= 0")
    check('Download everything' in pg.inner_text('#offDl'), 'menu shows download control with size: ' + pg.inner_text('#offDl'))
    pg.click('#offDl'); pg.wait_for_function("document.querySelector('#offMsg').textContent.indexOf('Downloading') >= 0", timeout=60000)
    pg.screenshot(path=S + 'pwa_download_progress.png')
    pg.wait_for_function("/Done|stopped/.test(document.querySelector('#offMsg').textContent)", timeout=900000)
    msg = pg.inner_text('#offMsg'); check(msg.startswith('Done'), 'full offline download completes: ' + msg)
    pg.wait_for_function("document.querySelector('#offStat').textContent.indexOf('Everything is saved') >= 0", timeout=20000)
    st = pg.inner_text('#offStat'); check('Everything is saved' in st, st)
    n = pg.evaluate("caches.open('sb-data').then(c => c.keys()).then(k => k.length)"); check(n + len(of['shell']) == len(of['files']), f'data cache holds all {n} files (+{len(of["shell"])} precached with the app)')
    pg.screenshot(path=S + 'pwa_download_done.png')
    ctx.set_offline(True)
    for r in ['Isa/40', 'Ps/22', 'Sir/24', 'DanOG/7', 'TobS/3']:
        pg.goto(B + '#/' + r); pg.wait_for_selector('.verse', timeout=10000)
    pg.goto(B + '#/Isa/40'); pg.wait_for_selector('.verse'); pg.keyboard.press('Escape'); pg.locator('.verse .w').nth(3).click(); pg.wait_for_selector('#panel:not([hidden]) .sum')
    pg.click('#panel .moreb') if pg.locator('#panel .moreb').count() else None
    check(pg.locator('.verse').count() > 20, 'offline after download: unvisited chapters load (Isa 40, Ps 22, Sir 24, DanOG 7, TobS 3) and word card opens')
    lat = [k for k in of['files'] if any(k.startswith('data/' + x) for x in ('vul', 'latw', 'latlex', 'vulg_words'))]
    check(not lat and of['total'] < 45e6, f'offline list has no Latin files; total {of["total"]/1e6:.1f} MB')
    pg.goto(B + '#/search?q=logos'); pg.wait_for_timeout(1200); check(pg.locator('.res').count() > 0, 'offline: vocabulary search works')
    ctx.set_offline(False)
    pg.goto(B + '#/Gen/1'); pg.wait_for_selector('.w'); pg.click('#menuBtn'); pg.wait_for_selector('#offClr:not([hidden])')
    pg.once('dialog', lambda d: d.accept()); pg.click('#offClr'); pg.wait_for_function("document.querySelector('#offMsg').textContent.indexOf('removed') >= 0")
    check(pg.evaluate("caches.open('sb-data').then(c => c.keys()).then(k => k.length)") == 0, 'remove offline data empties the data cache')
    check(not errs, f'no JS errors ({errs[:3]})')
    br.close()
print(f'\n{len(ok)} passed, {len(fails)} failed'); [print(' -', f) for f in fails]

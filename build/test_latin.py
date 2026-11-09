"""Playwright tests for the Latin layer (study-bible-latin). Usage: serve site/ (e.g. python3 -m http.server 8766), then python3 build/test_latin.py [base-url] [shots-dir]"""
import json, sys, os, urllib.request
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8766/'
S = sys.argv[2] if len(sys.argv) > 2 else '/workspace/lxx-nt/test/shots/latin_'
os.makedirs(os.path.dirname(S), exist_ok=True)
errs, fails = [], []
def check(c, m): (None if c else fails.append(m)); print(('PASS ' if c else 'FAIL ') + m)
def mode(p, m): p.locator(f'.modebar [data-mode="{m}"]').first.click(); p.wait_for_timeout(500)
with sync_playwright() as pw:
    br = pw.chromium.launch()
    for name, vp in [('phone', {'width': 360, 'height': 800}), ('desktop', {'width': 1280, 'height': 900})]:
        p = br.new_page(viewport=vp, device_scale_factor=2 if name == 'phone' else 1)
        p.on('pageerror', lambda e: errs.append(str(e))); p.on('console', lambda m: m.type == 'error' and errs.append(m.text))
        p.goto(B + '#/Gen/1'); p.wait_for_selector('.w')
        check(p.locator('.modebar button').count() == 5, f'{name}: five modes')
        mb = p.locator('.modebar').bounding_box(); check(mb['x'] >= 0 and mb['x'] + mb['width'] <= vp['width'] + 1, f'{name}: mode bar fits the screen ({int(mb["width"])}px)')
        # Greek card: Latin line only for a confident match
        p.locator('#v1 .w', has_text='θεὸς').first.click(); p.wait_for_selector('#sla:not([hidden])'); t = p.inner_text('#sla')
        check('Deus' in t and 'automatic match' in t, f'{name}: Greek card θεὸς shows Vulgate Deus ({t!r})')
        p.keyboard.press('Escape'); p.locator('#v1 .w', has_text='ἀρχῇ').first.click(); p.wait_for_selector('#panel:not([hidden]) .sum'); p.wait_for_timeout(900)
        check(p.locator('#sla').is_hidden(), f'{name}: no Latin line where the match is not confident (ἀρχῇ)'); p.keyboard.press('Escape')
        mode(p, 'latin'); p.wait_for_selector('.lverse')
        check(p.locator('.en.dr').first.is_hidden() and 'In principio' in p.inner_text('.lverse >> nth=0'), f'{name}: Latin mode shows the Vulgate only')
        p.locator('.lw', has_text='Deus').first.click(); p.wait_for_selector('#panel:not([hidden]) .sum.lat'); t = p.inner_text('#panelBody')
        check('deus' in t and 'God' in t and 'hand-checked' in t and 'noun' in t, f'{name}: Latin card Deus: lemma, hand-checked meaning, parse')
        p.screenshot(path=f'{S}{name}_latin_gen1_deus.png'); p.keyboard.press('Escape')
        mode(p, 'latin-en'); p.wait_for_selector('.en.dr'); check('In the beginning God created' in p.inner_text('.lverse >> nth=0'), f'{name}: Latin + English (Douay-Rheims)')
        p.screenshot(path=f'{S}{name}_latin_en_gen1.png')
        mode(p, 'latin-gk'); p.goto(B + '#/Ps/22'); p.wait_for_selector('.verse.pair')
        check(p.locator('.verse.pair .gk').count() > 3 and p.locator('.verse.pair .la').count() > 3, f'{name}: Latin + Greek pairs verses (Ps 22)')
        p.screenshot(path=f'{S}{name}_latin_gk_ps22.png')
        p.goto(B + '#/Tob/1'); p.wait_for_selector('.lverse'); check(p.locator('.verse.pair').count() == 0 and 'Aramaic' in p.inner_text('#main'), f'{name}: Tobit is single-text with a note')
        for bk in ('Jdt/1', 'Sir/1', 'Jer/1'):
            p.goto(B + '#/' + bk); p.wait_for_selector('.lverse'); check(p.locator('.verse.pair').count() == 0, f'{name}: {bk} single-text in Latin + Greek')
        p.goto(B + '#/Prov/31'); p.wait_for_selector('.lverse'); check('Proverbs 30' in p.inner_text('h1') and 'Proverbs 31' in p.inner_text('h1'), f'{name}: content map: our Prov 31 shows Vulgate Prov 30 + 31')
        p.goto(B + '#/4Esdr/1'); p.wait_for_selector('.lmiss, .lverse'); t = p.inner_text('#main')
        check('Greek original is lost' in t and ('not included yet' in t or p.locator('.lverse').count() > 0), f'{name}: 4 Esdras: Latin-only note, no broken page')
        p.goto(B + '#/Joel/3'); p.wait_for_selector('.lmiss'); check('Joel 2:28' in p.inner_text('.lmiss'), f'{name}: content map note: LXX Joel 3 = Vulgate Joel 2:28-32')
        p.goto(B + '#/3Macc/1'); p.wait_for_selector('.lmiss'); check('not in the Vulgate' in p.inner_text('.lmiss'), f'{name}: 3 Maccabees: not-in-Vulgate note')
        p.goto(B + '#/PrMan/1'); p.wait_for_selector('h1'); check('Prayer of Manasseh (Odes 12)' in p.inner_text('h1'), f'{name}: PrMan title')
        mode(p, 'reader'); p.goto(B + '#/Tob/1'); p.wait_for_selector('.w'); p.locator('.w').nth(3).click(); p.wait_for_selector('#panel:not([hidden]) .sum'); p.wait_for_timeout(800)
        check(p.locator('#sla').is_hidden(), f'{name}: no Latin line in the Greek card for Tobit'); p.keyboard.press('Escape')
        p.goto(B + '#/'); p.wait_for_selector('#hs1'); names = [x.inner_text().split('\n')[0] for x in p.locator('#hs1 .bn').all()]
        check(len(names) > 2 and names[0].startswith('1 Esdras') and names[1].startswith('4 Esdras'), f'{name}: home: 4 Esdras right after 1 Esdras ({names[:3]})')
        check(any('Prayer of Manasseh (Odes 12)' in n for n in names) and p.locator('.hsec').count() == 3, f'{name}: home: three sections, PrMan named')
        p.screenshot(path=f'{S}{name}_home.png', full_page=False)
        p.goto(B + '#/search?q=verbum'); p.wait_for_selector('.lres'); p.locator('.lres').first.click(); p.wait_for_selector('#results .refs a')
        p.locator('#results .refs a').first.click(); p.wait_for_selector('.lw.same'); check(p.locator('.lw.same').count() >= 1, f'{name}: Latin search → verse with the word marked')
        mode(p, 'reader'); p.close()
    bk = json.load(urllib.request.urlopen(B + 'data/books.json'))
    check(not any(b.get('latinOnly') and os.path.exists('data/' + b['id']) for b in bk), 'latin-only books have no Greek chapter files (expected)')
    check(not errs, f'no JS errors {errs[:3]}')
print(f'{len(fails)} failed'); sys.exit(1 if fails else 0)

"""Playwright tests for the clean-license preview (adapted from test_site.py). Usage: serve site/ on :8766, then python3 test_site.py"""
import json, re, sys, urllib.request, urllib.parse
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8766/'
S = '/workspace/lxx-nt/test/shots/'
errs, fails, ok = [], [], []
import unicodedata as _u; N = lambda x: _u.normalize('NFC', x)
def check(cond, msg):
    (ok if cond else fails).append(msg); print(('PASS ' if cond else 'FAIL ') + msg)
def word(p, text, verse=None, expand=True):
    loc = (p.locator(f'#v{verse} .w', has_text=text) if verse else p.locator('.w', has_text=text)).first
    if p.locator('#panel.exp:not([hidden])').count() and p.viewport_size['width'] < 1000: p.locator('#moreBtn').click(); p.wait_for_timeout(250)
    loc.click(); p.wait_for_selector('#panel:not([hidden]) .sum')
    p.wait_for_selector('#mtabs .tab', state='attached'); p.wait_for_timeout(400)
    if expand and p.locator('#more').is_hidden(): p.locator('#moreBtn').click(); p.wait_for_timeout(250)
    return p.inner_text('#panelBody')
with sync_playwright() as pw:
    br = pw.chromium.launch()
    for name, vp in [('desktop', {'width': 1366, 'height': 900}), ('phone', {'width': 390, 'height': 844})]:
        p = br.new_page(viewport=vp, device_scale_factor=2 if name == 'phone' else 1)
        p.on('pageerror', lambda e: errs.append(str(e))); p.on('console', lambda m: m.type == 'error' and errs.append(m.text))
        def shot(n, opens=()):
            for sel in opens:
                if p.locator(sel).count(): p.locator(sel).first.click(); p.wait_for_timeout(150)
            p.screenshot(path=f'{S}{name}_{n}.png')
        p.goto(B + '#/Gen/1'); p.wait_for_selector('.w')
        t = word(p, 'ἀρχῇ', 1, False)
        check(p.locator('#more').is_hidden() and '221' in t and 'beginning' in t and 'noun: dative singular feminine' in t.lower() and 'Abbott-Smith' not in t, f'{name} compact first view: lemma, gloss, one-line parse only')
        check(p.inner_text('#sfreq').strip() == '221', f'{name} compact LXX frequency at right')
        box = p.locator('#panel').bounding_box(); check(box['height'] < vp['height'] * 0.42, f'{name} compact panel height {int(box["height"])}px')
        p.screenshot(path=f'{S}{name}_compact_gen1_arche.png')
        p.locator('#moreBtn').click(); p.wait_for_timeout(250); t = p.inner_text('#panelBody')
        check(p.locator('#more').is_visible(), f'{name} More expands detail')
        p.screenshot(path=f'{S}{name}_expanded_gen1_arche.png')
        check('beginning' in t and 'dative' in t and 'Abbott-Smith' in t and 'LSJ' in t, f'{name} ἀρχῇ: two meaning sources + chips')
        check('ἄρχω' in t and 'CC BY-SA' in t, f'{name} ἀρχῇ etymology (Wiktionary layer, labelled)')
        check(p.locator('#latRow').count() == 0 and p.locator('#sla').is_hidden(), f'{name} no Latin line for ἀρχῇ (no confident Vulgate match)')
        p.locator('.rc', has_text='Lit.').click(); check('Homer' in p.inner_text('#refOpen'), f'{name} ἀρχῇ literature ref chip (LSJ) expands')
        p.locator('#mtabs .tab', has_text='LSJ').click(); check('foundation' in p.inner_text('#mbody'), f'{name} LSJ tab switches')
        p.locator('#mtabs .tab').first.click()
        shot('gen1_arche_noun', ['#formsRow summary'])
        check(p.locator('#pdBox .pf.cur').count() >= 1, f'{name} ἀρχῇ current form highlighted')
        t = word(p, 'ἐποίησεν', 1)
        check('aorist' in t and 'active' in t and 'indicative' in t, f'{name} ἐποίησεν parse chips')
        p.locator('.chip[data-g="aorist"]').click(); check('simple whole event' in p.inner_text('#gexp'), f'{name} aorist tooltip')
        check('Reads like' not in t and 'Quoted in' not in t, f'{name} no long prose in panel')
        shot('gen1_epoiesen_verb', ['#formsRow summary'])
        check(p.locator('#pdBox details.pg[open] .pf.cur').count() >= 1, f'{name} ἐποίησεν highlighted in verb table')
        p.goto(B + '#/Ps/22'); p.wait_for_selector('#v1 .w')
        t = word(p, 'ποιμαίνει', 1); check('present' in t and 'shepherd' in t.lower(), f'{name} ποιμαίνει present, shepherd')
        shot('ps22_poimainei')
        p.goto(B + '#/Ps/32'); p.wait_for_selector('.w'); word(p, 'λόγῳ'); check('word' in p.inner_text('.sdef') and 'LXX lexicon' not in p.text_content('#panelBody') and 'CCAT' not in p.text_content('#panelBody'), f'{name} clean: no LXX-lexicon/CCAT meaning on the card')
        p.close()
    p = br.new_page(viewport={'width': 390, 'height': 844}, device_scale_factor=2, color_scheme='dark')
    p.on('pageerror', lambda e: errs.append(str(e)))
    p.goto(B + '#/Gen/1'); p.wait_for_selector('.w'); t = word(p, 'ἐποίησεν', 1, False); check('verb: aorist active indicative' in t.lower() and p.locator('#more').is_hidden(), 'fresh phone: compact verb parse line'); p.screenshot(path=f'{S}phone_dark_gen1.png')
    p.goto(B + '#/about'); p.wait_for_selector('article'); a = p.inner_text('article')
    check('TFLSJ' in a and 'CC BY-SA' in a and 'Wiktionary' in a, 'about: LSJ + Wiktionary attribution')
    bk = json.load(urllib.request.urlopen(B + 'data/books.json')); bad = []; n = 0
    for b in bk:
        if b.get('latinOnly'): continue   # Latin-only book (4 Esdras): no Greek chapter files; its Latin is tested in test_latin.py
        for c in b['chapters']:
            n += 1
            try: json.load(urllib.request.urlopen(B + f'data/{b["id"]}/{c}.json'))
            except Exception: bad.append(f'{b["id"]}/{c}')
    check(not bad, f'all {n} chapter files load')
    p2 = br.new_page(); p2.on('pageerror', lambda e: errs.append(str(e)))
    for b in [x for x in bk if not x.get('latinOnly')][::3]:
        p2.goto(B + f'#/{b["id"]}/{b["chapters"][-1]}'); p2.wait_for_selector('.verse'); p2.locator('.w').first.click(); p2.wait_for_selector('#panel:not([hidden]) .sum')
    check(True, f'clicked a word in {len(bk[::3])} books')
    p3 = br.new_page(viewport={'width': 1280, 'height': 900}); p3.on('pageerror', lambda e: errs.append(str(e)))
    p3.goto(B + '#/Gen/1'); p3.wait_for_selector('.en1'); p3.wait_for_timeout(800)
    check(p3.title() == 'Genesis 1 — Gallicantus' and p3.inner_text('.brand') == 'Gallicantus', 'verse page: title and header are Gallicantus')
    p3.evaluate("localStorage.setItem('lxx-entr', 'lxx2012')"); p3.reload(); p3.wait_for_selector('.en1'); p3.wait_for_timeout(400)
    check(p3.locator('.en1').first.is_visible() and p3.locator('.en2').count() == 0 and p3.locator('#enSel').count() == 0 and p3.locator('#enBtn').count() == 0 and p3.locator('.ensel').count() == 0, 'English: Brenton only; no selector or EN button; saved LXX2012 choice shows Brenton')
    check(p3.evaluate("localStorage.getItem('lxx-entr')") is None, 'saved LXX2012 choice migrated (removed)')
    for old in ['bx', 'x', '0']:
        p3.evaluate("k => localStorage.setItem('lxx-en', k)", old); p3.reload(); p3.wait_for_selector('.en1'); p3.wait_for_timeout(400)
        check(p3.locator('.en1').first.is_visible() and p3.locator('.en2').count() == 0, f"old saved lxx-en='{old}' ignored: Brenton shown")
    check(p3.locator('.modebar [data-mode=greek]').count() == 1 and p3.locator('.modebar [data-mode=reader]').count() == 1 and p3.locator('.modebar button').count() == 5, 'Greek | Greek+English tabs kept, plus three Latin modes')
    # --- LXX2012 line in the word pop-up only ---
    p3.goto(B + '#/EpJer/1'); p3.wait_for_selector('#v8 .w'); p3.locator('#v8 .w').first.click(); p3.wait_for_selector('#slx:not([hidden])'); t = p3.inner_text('#slx')
    check('LXX2012' in t and 'alternate rendering' in t and 'silver' in t and 'laid over with silver' not in p3.inner_text('#v8'), 'pop-up: allowlisted LXX2012 alternate rendering (EpJer 1:8), not in the verse view')
    p3.keyboard.press('Escape')
    p3.goto(B + '#/Deut/14'); p3.wait_for_selector('#v15 .w'); p3.locator('#v15 .w').first.click(); p3.wait_for_selector('#panel:not([hidden]) .sum'); p3.wait_for_timeout(700)
    check(p3.locator('#slx').is_hidden(), 'pop-up: no LXX2012 line for a verse that is not on the allowlist (Deut 14:15)'); p3.keyboard.press('Escape')
    lxn = sum(len(json.load(urllib.request.urlopen(B + 'data/lx/' + c + '.json'))) for c in json.load(urllib.request.urlopen(B + 'data/lx/index.json')))
    check(lxn == 7, f'LXX2012 lines: exactly the 7 allowlisted ({lxn})')
    # --- Latin-letter search for NT-only headwords ---
    for q, want in [('chalkedon', 'χαλκηδών'), ('sardonux', 'σαρδόνυξ'), ('pelekizo', 'πελεκίζω'), ('logos', 'λόγος')]:
        p3.goto(B + '#/search?q=' + q); p3.wait_for_selector('#results .res, #results p'); p3.wait_for_timeout(200)
        check(N(want) in N(p3.inner_text('#results')), f'Latin-letter search {q!r} finds {want}')
    # --- lemma grouping: εἶπον under λέγω ---
    p3.goto(B + '#/Matt/3'); p3.wait_for_selector('#v15 .w'); w = [x for x in p3.locator('#v15 .w').all() if N('εἶπεν') in N(x.inner_text())]
    if not w: p3.goto(B + '#/Matt/4'); p3.wait_for_selector('#v3 .w'); w = [x for x in p3.locator('#v3 .w').all() if N('εἶπεν') in N(x.inner_text())]
    w[0].click(); p3.wait_for_selector('#panel:not([hidden]) .sum'); p3.wait_for_timeout(800); pt = p3.inner_text('#panel')
    check(N('λέγω') in N(pt) and 'aorist' in pt.lower(), 'grouping: εἶπεν shows headword λέγω and keeps its aorist tag')
    if p3.locator('#more').is_hidden(): p3.click('#moreBtn')
    p3.locator('#formsRow summary').first.click(); p3.wait_for_timeout(300); pd = N(p3.text_content('#pdBox'))
    check(N('εἶπεν') in pd and N('λέγει') in pd, 'grouping: λέγω forms table has εἶπεν and λέγει'); p3.keyboard.press('Escape')
    p3.goto(B + '#/John/1'); p3.wait_for_selector('#v26 .w'); w = [x for x in p3.locator('#v26 .w').all() if N('οἴδατε') in N(x.inner_text())]
    w[0].click(); p3.wait_for_selector('#panel:not([hidden]) .sum'); p3.wait_for_timeout(500); check(N('οἶδα') in N(p3.inner_text('.slem')), 'grouping: οἴδατε shows headword οἶδα'); p3.keyboard.press('Escape')
    # --- dictionary tab named after its real source ---
    p3.goto(B + '#/John/1'); p3.wait_for_selector('#v1 .w'); p3.locator('#v1 .w').nth(4).click(); p3.wait_for_selector('#mtabs .tab', state='attached'); p3.wait_for_timeout(400)
    if p3.locator('#more').is_hidden(): p3.click('#moreBtn')
    check(p3.inner_text('#mtabs .tab >> nth=0') == 'Abbott-Smith' and 'Abbott-Smith (corrected by Tyndale House), via STEPBible TBESG' in p3.inner_text('#panel'), 'dictionary tab: λόγος = Abbott-Smith, source line says so'); p3.keyboard.press('Escape')
    # --- word sheet: count never under the A−/A+/✕ buttons ---
    def ov(a, b): return a and b and not (a['x'] + a['width'] <= b['x'] or b['x'] + b['width'] <= a['x'] or a['y'] + a['height'] <= b['y'] or b['y'] + b['height'] <= a['y'])
    for vw, vh in [(412, 915), (360, 800), (1280, 800)]:
        pp = br.new_page(viewport={'width': vw, 'height': vh}); pp.goto(B + '#/Gen/1'); pp.evaluate("localStorage.setItem('lxx-pfs','1.4')"); pp.reload(); pp.wait_for_selector('#v1 .w')
        pp.locator('#v1 .w').first.click(); pp.wait_for_function("document.querySelector('#sfreq') && document.querySelector('#sfreq').textContent.length>0"); pp.wait_for_timeout(300)
        if pp.locator('#more').is_hidden(): pp.click('#moreBtn'); pp.wait_for_timeout(300)
        sf = pp.locator('#sfreq').bounding_box(); bad = [x for x in ('#pSmaller', '#pLarger', '#panelClose') if pp.locator(x).is_visible() and ov(sf, pp.locator(x).bounding_box())]
        check(not bad, f'word sheet {vw}x{vh}: count clear of A−/A+/✕ ({bad})'); pp.close()
    p3.goto(B + '#/Gen/1'); p3.wait_for_selector('#v1 .w'); p3.locator('#v1 .w').nth(1).click(); p3.wait_for_selector('#panel:not([hidden]) .sum'); p3.wait_for_timeout(700)
    check(p3.locator('#slx').is_hidden(), 'pop-up: no LXX2012 line where it does not differ meaningfully (Gen 1:1)'); p3.keyboard.press('Escape')
    lx = json.load(urllib.request.urlopen(B + 'data/lx/index.json')); check(1 <= len(lx) <= 7, f'lx index: {len(lx)} chapters')
    # --- New Testament ---
    bkj = json.load(urllib.request.urlopen(B + 'data/books.json')); nt = [b for b in bkj if b.get('nt')]
    check(len(nt) == 27 and sum(len(b['chapters']) for b in nt) == 260, f'NT: 27 books, 260 chapters ({len(nt)}, {sum(len(b["chapters"]) for b in nt)})')
    p3.goto(B + '#/John/1'); p3.wait_for_selector('#v1 .w'); p3.wait_for_timeout(300)
    import unicodedata as _u; N = lambda x: _u.normalize('NFC', x)
    check(N(p3.inner_text('#v1 .gk')).replace('1','',1).strip().startswith(N('Ἐν ἀρχῇ ἦν ὁ λόγος')) and 'In the beginning was the Word' in p3.inner_text('#v1 .en3'), 'NT: John 1:1 Greek + WEB English')
    check(p3.locator('#enSel').count() == 0 and p3.locator('.ensel').count() == 0, 'NT: no English selector')
    p3.locator('#v1 .w').nth(4).click(); p3.wait_for_selector('#panel:not([hidden]) .sum'); p3.wait_for_timeout(400)
    pt = p3.inner_text('#panel'); check(N('λόγος') in N(pt) and 'nominative singular masculine' in pt.lower(), 'NT: word card shows lemma and grammar (TAGNT)')
    p3.wait_for_function("document.querySelector('#freqChip') && /NT/.test(document.querySelector('#freqChip').textContent)")
    check(p3.inner_text('#freqChip').strip() == '1177× LXX · 330× NT' and p3.inner_text('#sfreq').strip() == '330', f"NT: λόγος counts LXX + NT ({p3.inner_text('#freqChip')!r}, top {p3.inner_text('#sfreq')!r})")
    if p3.locator('#more').is_hidden(): p3.click('#moreBtn')
    p3.locator('#formsRow summary').first.click(); p3.wait_for_timeout(300)
    check(N('λόγου') in N(p3.inner_text('#pdBox')) and N('λόγοι') in N(p3.inner_text('#pdBox')), 'NT: forms table includes forms (λόγου, λόγοι)')
    p3.keyboard.press('Escape')
    p3.goto(B + '#/Matt/1'); p3.wait_for_selector('#v1 .w'); p3.locator('#v1 .w').nth(0).click(); p3.wait_for_selector('#panel:not([hidden]) .sum'); p3.wait_for_timeout(900)
    check('NT' in p3.inner_text('#freqChip'), f"NT: βίβλος card has an NT count ({p3.inner_text('#freqChip')!r})"); p3.keyboard.press('Escape')
    p3.goto(B + '#/search?q=' + 'αγαπη'); p3.wait_for_selector('.res'); rt = p3.inner_text('#results')
    check('116× NT' in rt, f'search: ἀγάπη shows NT count ({rt[:120]!r})')
    p3.goto(B + '#/search?lex=48'); p3.wait_for_selector('#results .grp'); ot = p3.inner_text('#results')
    ot = ot.upper(); check('MATTHEW' in ot and 'GENESIS' not in ot.split('MATTHEW')[1] and '(1177 IN THE LXX, 330 IN THE NT)' in ot, 'search: λόγος occurrences list NT books after LXX books, with split counts')
    p3.goto(B + '#/Matt/17'); p3.wait_for_selector('#v22'); check(p3.locator('#v21').count() == 0 and 'Not in the NA28' not in p3.inner_text('#main'), 'NT: Matt 17:21 (not in NA28) is gone: no verse, no note')
    p3.click('.modebar [data-mode=greek]'); check(p3.locator('.en:visible').count() == 0, 'NT: Greek tab hides English'); p3.click('.modebar [data-mode=reader]')
    # --- Apocrypha labels ---
    p3.goto(B + '#/Tob/1'); p3.wait_for_selector('.apocnote'); check('Apocrypha' in p3.inner_text('.apocnote') and 'deuterocanonical' in p3.inner_text('.apocnote').lower(), 'Apocrypha: Tobit chapter labelled')
    p3.goto(B + '#/Gen/1'); p3.wait_for_selector('.w'); check(p3.locator('.apocnote').count() == 0, 'Apocrypha: Genesis not labelled')
    p3.click('#menuBtn'); check(p3.locator('#bookList .apoc').count() == 0 and [x.text_content().strip() for x in p3.locator('#bookList .grp').all()] == ['Septuagint', 'Apocrypha', 'New Testament'] and p3.locator('.grp', has_text='Poetry').count() == 0, 'book list: three sections matching home, no Apocrypha tags, no Poetry & Wisdom'); p3.keyboard.press('Escape')
    p3.click('.modebar [data-mode=greek]'); check(p3.locator('.en:visible').count() == 0, 'Greek tab hides English')
    p3.click('.modebar [data-mode=reader]'); check(p3.locator('.en1').first.is_visible(), 'Reader tab shows Brenton')
    p3.goto(B + '#/about'); p3.wait_for_selector('article'); a3 = p3.inner_text('article')
    check(p3.inner_text('.about h1').split('\n')[0].strip() == 'About Gallicantus' and p3.inner_text('.about h1 .asub') == 'Greek-Latin Study Bible' and 'The Greek Septuagint' in a3 and p3.title() == 'About — Gallicantus', 'about: heading About Gallicantus with Greek-Latin Study Bible subtitle; Septuagint kept as the Greek OT')
    check('LXX2012' in a3 and 'Morpheus' in a3 and 'TAGNT' in a3 and 'CCAT' not in a3 and 'NC' not in a3.replace('NCE','') , 'about: clean credits (Brenton Greek, Morpheus, TAGNT; no CCAT)')
    check('World English Bible' in a3 and 'STEPBible' in a3.replace('STEP Bible','STEPBible') and not any(k.startswith('data/en2/') for k in json.load(urllib.request.urlopen(B + 'offline-files.json'))['files']) and 'data/lx/index.json' in json.load(urllib.request.urlopen(B + 'offline-files.json'))['files'], 'en2 data loads')
    p6 = br.new_page(); p6.on('pageerror', lambda e: errs.append(str(e))); lat_req = []
    p6.on('request', lambda r: lat_req.append(r.url) if any(x in r.url for x in ('/vul/', '/latw/', 'latlex', 'vulg_words')) else None)
    p6.goto(B + '#/Ps/22'); p6.wait_for_selector('.w'); p6.locator('.w').nth(4).click(); p6.wait_for_selector('#panel:not([hidden]) .sum'); p6.wait_for_timeout(800)
    check(p6.locator('.lverse, .verse .la').count() == 0 and not any('/latw/' in u or 'vulg_words' in u for u in lat_req), f'Greek + English mode: no Latin verses in the text; no old Latin files requested ({lat_req[:2]})')
    p6.goto(B + '#/about'); p6.wait_for_selector('article'); ab = p6.inner_text('article')
    check('Wiktionary' in ab and 'grcbrent' in ab and 'Rahlfs 1935 via' not in ab, 'about: Brenton Greek credit, Wiktionary layer credit')
    p6.close()
    # --- reading modes ---
    p7 = br.new_page(viewport={'width': 390, 'height': 844}, device_scale_factor=2); p7.on('pageerror', lambda e: errs.append(str(e)))
    p7.goto(B + '#/Gen/1'); p7.evaluate("localStorage.removeItem('lxx-mode')"); p7.reload(); p7.wait_for_selector('.modebar')
    check(p7.get_attribute('.modebar [data-mode=reader]', 'aria-pressed') == 'true' and p7.locator('.en1').first.is_visible(), 'modes: Reader is the default, English visible')
    p7.screenshot(path=f'{S}mode_phone_reader_gen1.png')
    p7.click('.modebar [data-mode=greek]')
    check(p7.get_attribute('.modebar [data-mode=greek]', 'aria-pressed') == 'true' and p7.locator('.en:visible').count() == 0 and not p7.locator('#enBtn').is_visible(), 'modes: Greek hides all English and the EN button')
    check('In the beginning' not in p7.inner_text('#main'), 'modes: no English text readable in Greek mode')
    p7.screenshot(path=f'{S}mode_phone_greek_gen1.png')
    p7.locator('.w', has_text='ἐποίησεν').first.click(); p7.wait_for_selector('#panel:not([hidden]) .sum'); p7.wait_for_timeout(300)
    check('ποιέω' in __import__('unicodedata').normalize('NFC', p7.inner_text('#panel')), 'modes: word card opens in Greek mode')
    p7.screenshot(path=f'{S}mode_phone_greek_card.png'); p7.keyboard.press('Escape')
    p7.reload(); p7.wait_for_selector('.modebar'); check(p7.get_attribute('.modebar [data-mode=greek]', 'aria-pressed') == 'true' and p7.locator('.en:visible').count() == 0, 'modes: preference persists after reload')
    p7.goto(B + '#/Gen/1/20'); p7.wait_for_timeout(600); p7.keyboard.press('Escape')
    def topv(): return p7.evaluate("(() => { const y0 = document.querySelector('.modestrip').getBoundingClientRect().bottom; return [...document.querySelectorAll('.verse')].find(v => v.getBoundingClientRect().bottom > y0 + 4).id })()")
    before = topv(); check(p7.locator('.modebar').is_visible() and p7.locator('.modebar').bounding_box()['y'] < 150, 'modes: switch stays reachable when scrolled (sticky)')
    p7.click('.modebar [data-mode=reader]'); p7.wait_for_timeout(300)
    after = topv(); check(before == after, f'modes: reading position kept when switching ({before} -> {after})')
    p7.evaluate("document.querySelector('.modebar [data-mode=greek]').click()"); p7.wait_for_timeout(300); check(topv() == before, f'modes: position kept switching back ({topv()})')
    p7.goto(B + '#/Gen/1'); p7.wait_for_selector('.modebar'); p7.focus('.modebar [data-mode=greek]'); p7.keyboard.press('Enter'); p7.wait_for_timeout(200)
    check(p7.get_attribute('.modebar [data-mode=greek]', 'aria-pressed') == 'true', 'modes: keyboard (Tab/Enter) switches mode')
    p7.evaluate("localStorage.removeItem('lxx-mode')"); p7.close()
    p8 = br.new_page(viewport={'width': 1440, 'height': 900}); p8.goto(B + '#/Gen/1'); p8.wait_for_selector('.en1')
    g = p8.locator('#v1 .gk').bounding_box(); e = p8.locator('#v1 .en1').bounding_box()
    check(e['x'] > g['x'] + g['width'] - 5, 'modes: Reader is side by side on wide screens'); p8.screenshot(path=f'{S}mode_desk_reader_gen1.png'); p8.close()
    # --- Brenton's wording ---
    p9 = br.new_page(viewport={'width': 390, 'height': 844}, device_scale_factor=2); p9.on('pageerror', lambda e: errs.append(str(e)))
    p9.goto(B + '#/Gen/1'); p9.evaluate("localStorage.setItem('lxx-mode','reader')"); p9.reload(); p9.wait_for_selector('#v2 .en1')
    p9.locator('#v2 .w', has_text='ἀόρατος').click(); p9.wait_for_selector('#sbw:not([hidden])'); sb = p9.inner_text('#sbw')
    check('unsightly' in sb and 'likely match' in sb and 'plain meaning' not in sb and 'invisible' in p9.inner_text('#panel .sdef'), f'bw: ἀόρατος -> Brenton “unsightly”, plain “invisible”, no commentary ({sb!r})')
    check(p9.locator('#v2 mark.bw').inner_text() == 'unsightly', 'bw: “unsightly” highlighted in the Brenton verse')
    p9.evaluate("document.querySelector('#v2').scrollIntoView({block:'start'})"); p9.evaluate("window.scrollBy(0,-120)"); p9.wait_for_timeout(200)
    p9.screenshot(path=f'{S}bw2_phone_reader_differs_gen1_2.png')
    p9.locator('#v1 .w', has_text='γῆν').click(); p9.wait_for_function("(document.querySelector('#sbw')||{}).textContent && document.querySelector('#sbw').textContent.indexOf('earth') >= 0")
    check(p9.locator('mark.bw').count() == 1 and p9.locator('#v1 mark.bw').inner_text() == 'earth', 'bw: γῆν -> “earth”, old highlight cleared')
    p9.evaluate("window.scrollTo(0,0)"); p9.wait_for_timeout(200); p9.screenshot(path=f'{S}bw2_phone_reader_card_highlight.png')
    p9.locator('#v2 .w', has_text='ἐπεφέρετο').click(); p9.wait_for_timeout(800)
    check(p9.locator('mark.bw').count() == 0 and p9.evaluate("(function(b){return !b || (b.hidden && !b.textContent.trim())})(document.querySelector('#sbw'))") and 'confident' not in p9.locator('#card, body').first.inner_text(), 'bw: low confidence -> no Brenton line at all, nothing highlighted')
    p9.evaluate("document.querySelector('#v2').scrollIntoView({block:'start'})"); p9.evaluate("window.scrollBy(0,-120)"); p9.wait_for_timeout(200); p9.screenshot(path=f'{S}bw3_phone_no_match_gen1_2.png')
    p9.locator('#v1 .w', has_text='τὸν').first.click(); p9.wait_for_timeout(500); check(p9.locator('#sbw').is_hidden() and p9.locator('mark.bw').count() == 0, 'bw: article -> no Brenton row (by design)')
    p9.keyboard.press('Escape'); check(p9.locator('mark.bw').count() == 0, 'bw: closing the card removes the highlight')
    p9.evaluate("document.querySelector('.modebar [data-mode=greek]').click()"); p9.evaluate("window.scrollTo(0,0)")
    p9.locator('#v1 .w', has_text='ἐποίησεν').click(); p9.wait_for_selector('#sbw:not([hidden])'); p9.wait_for_timeout(300)
    check('made' in p9.inner_text('#sbw') and p9.locator('.en:visible').count() == 0, 'bw: Greek mode card shows Brenton’s word, English text still hidden')
    p9.screenshot(path=f'{S}bw2_phone_greek_card.png')
    # --- plain meaning (Dodson / STEP Bible) + other meanings + Also in the NT ---
    p9.evaluate("localStorage.setItem('lxx-mode','reader'); localStorage.setItem('lxx-exp','0')")
    def card(book, ch, v, form, shot=None, more=False):
        p9.goto(B + f'#/{book}/{ch}'); p9.reload(); p9.wait_for_selector(f'#v{v} .w')
        p9.locator(f'#v{v} .w', has_text=form).first.click(); p9.wait_for_selector('#panel .sdef'); p9.wait_for_timeout(600)
        if more: p9.click('#moreBtn'); p9.wait_for_timeout(300)
        p9.evaluate(f"document.querySelector('#v{v}').scrollIntoView({{block:'start'}})"); p9.evaluate("window.scrollBy(0,-120)"); p9.wait_for_timeout(200)
        if more: p9.evaluate("document.querySelector('#panel').scrollTop = 1e5"); p9.wait_for_timeout(200)
        if shot: p9.screenshot(path=f'{S}{shot}')
        r = (p9.inner_text('#panel .sdef'), p9.inner_text('#panel'))
        if more: p9.click('#moreBtn'); p9.evaluate("localStorage.setItem('lxx-exp','0')")
        return r
    d, _ = card('Gen', 1, 2, 'ἀόρατος', 'pl_phone_aoratos_gen1_2.png')
    check('invisible' in d and 'Dodson' in d and 'unsightly' in p9.inner_text('#sbw'), f'plain: ἀόρατος -> Dodson meaning + Brenton “unsightly” on one card ({d!r})')
    d, allt = card('Gen', 1, 2, 'ἐπεφέρετο', 'pl_phone_epiphero_gen1_2.png', more=True)
    check('Dodson' in d and 'inflict' not in d, f'plain: ἐπιφέρω headline from Dodson, not “inflict” ({d!r})')
    check('LXX lexicon' not in allt and 'STEP Bible' in allt and 'hand-picked' not in allt, 'plain: other meanings under More with source labels (no LXX lexicon, no automatic LXX sense)')
    d, _ = card('Gen', 1, 3, 'εἶπεν')
    check('say' in d, f'εἶπεν -> “say” ({d!r})')
    d, allt = card('Gen', 35, 3, 'θλίψεως', 'pl_phone_thlipsis_gen35_3.png')
    check('affliction' in d and 'Dodson' in d, f'plain: θλῖψις -> Dodson “…affliction…” ({d!r})')
    d, _ = card('Gen', 21, 17, 'Εἰσήκουσε', 'pl_phone_eisakouo_gen21_17.png')
    check('hear' in d and 'Dodson' in d, f'plain: εἰσακούω -> “hear, listen to” ({d!r})')
    d, _ = card('Gen', 1, 26, 'ἄνθρωπον', 'pl_phone_anthropos_gen1_26.png')
    check(d.startswith('man') and 'hand-written' in d, f'plain: ἄνθρωπος -> “man, human being” hand-written ({d!r})')
    d, allt = card('Gen', 9, 25, 'παῖς', more=True)
    check(d.startswith('servant; child, boy') and 'hand-written' in d and 'boy or girl child' in allt and 'Report a wrong meaning' in allt, f'preview: παῖς hand-written headline, Dodson kept under More, report link ({d!r})')
    d, allt = card('Gen', 32, 2, 'παρεμβεβληκυῖαν')
    check('encamp' in d and 'STEP Bible' in d, f'plain: παρεμβάλλω -> STEP Bible “encamp” (no Dodson entry) ({d!r})')
    d, allt = card('Gen', 35, 3, 'θλίψεως', 'pl_phone_nt_line_thlipsis.png', more=True)
    nt = p9.inner_text('#ntRow') if p9.locator('#ntRow:not([hidden])').count() else ''
    check('also in the nt' in allt.lower() and re.search(r'(Matt|Mark|John|Acts|Rom|Cor|Rev)', allt), f'plain: “Also in the NT” refs shown for θλῖψις ({allt[-160:]!r})')
    card('Gen', 35, 3, 'θλίψεως'); 
    p9.goto(B + '#/Gen/36'); p9.reload(); p9.wait_for_selector('#v2 .w')
    p9.locator('#v2 .w').nth(4).click(); p9.wait_for_timeout(600); p9.click('#moreBtn'); p9.wait_for_timeout(300)
    lid = p9.evaluate("document.querySelectorAll('#v2 .w')[4].dataset.l")
    has = p9.evaluate(f"fetch('data/nt.json').then(r=>r.json()).then(d=>!!d['{lid}'])")
    check(has or p9.locator('#ntRow').is_hidden(), 'plain: no NT line when the word is not in the NT')
    p9.click('#moreBtn'); p9.evaluate("localStorage.setItem('lxx-exp','0')")
    p9.evaluate("localStorage.removeItem('lxx-mode')")
    # --- clean-license: word with no dictionary form, Wiktionary layer word ---
    p9.goto(B + '#/1Chr/12'); p9.reload(); p9.wait_for_selector('#v13 .w'); p9.locator('#v13 .w', has_text='Ἐλιαζὲρ').first.click(); p9.wait_for_selector('#panel:not([hidden]) .sum'); p9.wait_for_timeout(700)
    pt = p9.inner_text('#panel'); check('Ἐλιαζὲρ' in pt and '—' not in pt and 'no match' not in pt.lower() and 'not found' not in pt.lower() and 'Dictionary form' not in pt and p9.locator('#moreBtn').count() == 0, f'no-lemma word: card shows only the word (+ Brenton) ({pt!r})')
    check('Eleazer' in (p9.inner_text('#sbw') if p9.locator('#sbw:not([hidden])').count() else ''), 'no-lemma name still gets Brenton’s word (Eleazer)')
    p9.goto(B + '#/Gen/12'); p9.reload(); p9.wait_for_selector('#v1 .w'); p9.locator('#v1 .w', has_text='Ἅβραμ').first.click(); p9.wait_for_selector('#panel:not([hidden]) .sum'); p9.wait_for_timeout(700)
    pt = p9.inner_text('#panel'); check('Ἅβραμ' in pt and 'Abram' in pt and 'Abraham' not in pt, f'approved name fill: Ἅβραμ shows Abram, not merged with Abraham ({pt!r})')
    p9.screenshot(path=f'{S}cl_nolemma_abram.png')
    p9.goto(B + '#/Gen/10'); p9.reload(); p9.wait_for_selector('#v1 .w[data-wk]'); p9.locator('#v1 .w').nth(8).click(); p9.wait_for_selector('#panel:not([hidden]) .sum'); p9.wait_for_timeout(500)
    p9.click('#moreBtn'); p9.wait_for_timeout(300); check('from Wiktionary, CC BY-SA 4.0' in p9.inner_text('#panel'), 'Wiktionary-layer word is labelled on the card'); p9.click('#moreBtn')
    nc = urllib.request.urlopen(B + 'NOTICE').read().decode(); check('Not used in this build' in nc and 'Morpheus' in nc and 'CC BY-SA' in nc, 'NOTICE: clean sources, separate CC BY-SA layer')
    # --- gaps round 2: confirmed rows + Brenton-checked fills + fix list (data/cx per-token layer) ---
    pg = br.new_page(viewport={'width': 412, 'height': 915}, device_scale_factor=2, is_mobile=True, has_touch=True)
    pg.on('pageerror', lambda e: errs.append(str(e)))
    def gcard(path, v, text):
        pg.goto(B + '#/' + path); pg.reload(); pg.wait_for_selector(f'#v{v} .w'); pg.locator(f'#v{v} .w', has_text=text).first.click()
        pg.wait_for_selector('#panel:not([hidden]) .sum'); pg.wait_for_timeout(900); return pg.inner_text('#panel')
    pt = gcard('Job/13', 11, 'δῖνα')
    check('whirlpool' in pt and 'meaning from context' in pt and pg.locator('#panelBody .gsrc.ctx').count() >= 1, f'context fill: δῖνα (Job 13:11) shows whirlpool with the "meaning from context" label ({pt[:160]!r})')
    pt = gcard('Josh/8', 11, 'ἐξεναντίας')
    check('opposite' in pt and 'meaning from context' in pt, f'context fill: ἐξεναντίας (Josh 8:11) labelled ({pt[:160]!r})')
    pt = gcard('Wis/14', 26, 'ἐναλλαγὴ')
    check('change, interchange' in pt and 'derived meaning' in pt and 'in this verse' in pt.lower() and 'interchange, changing' in pt, f'derived definition ἐναλλαγή tagged "derived meaning", verse meaning from context below ({pt[:200]!r})')
    pt = gcard('1Sam/29', 1, 'Ἀεδὼρ')
    check('Endor' in pt and 'name from context' in pt and 'LXX reads Endor' in pt and 'noun (name)' in pt.lower(), f'name: Ἀεδὼρ (1 Sam 29:1) → Endor, plain name entry with note ({pt[:220]!r})')
    if pg.locator('#moreBtn').count(): pg.click('#moreBtn'); pg.wait_for_timeout(500)
    check(pg.locator('#etyRow').is_hidden(), 'name entry: no etymology')
    pt = gcard('Lev/16', 5, 'χιμάρους')
    check('he-goat' in pt and 'winter yearling' not in pt, f'fixed definition: χίμαρος → he-goat ({pt[:120]!r})')
    pt = gcard('Amos/3', 2, 'διατοῦτο')
    check('διὰ τοῦτο' in pt and 'therefore' in pt and 'Two words run together' in pt and pg.locator('#scx .cxw').count() == 2, f'fusion: διατοῦτο shows διὰ τοῦτο with two dictionary links ({pt[:200]!r})')
    vt = json.loads(urllib.request.urlopen(B + 'data/Amos/3.json').read()); v2 = [v for v in vt if str(v[0]) == '2'][0]
    check(pg.locator('#v2 .w').count() == len(v2[1]) and v2[1][9][0] == 'διατοῦτο', 'fusion stays ONE token: verse word numbering (Latin/Brenton alignment indexes) unchanged')
    pg.locator('#scx .cxw').first.click(); pg.wait_for_timeout(700); pt = pg.inner_text('#panel')
    check(N(pg.inner_text('#panelBody .slem')).strip() == N('διά') and 'through' in pt, f'fusion part link opens the διά dictionary card ({pt[:120]!r})')
    import glob as _g2
    LX = json.load(open('data/lexicon.json')); WK = {}; blank = 0
    for fn in _g2.glob('data/wk/*/*.json'): WK[fn[8:-5]] = json.load(open(fn))
    for b in json.load(open('data/books.json')):
        if b.get('nt'): continue
        for ch in b['chapters']:
            try: vs = json.load(open(f'data/{b["id"]}/{ch}.json'))
            except FileNotFoundError: continue
            w = WK.get(f'{b["id"]}/{ch}', {})
            for v in vs:
                for i, t in enumerate(v[1]):
                    x = w.get(str(v[0]), {}).get(str(i)); lid = str(x[0] if x else t[1])
                    if not LX.get(lid, ['', ''])[1]: blank += 1
    check(blank == 248, f'audited Greek gap after round 2 + grammar pass: {blank} blank tokens (expected 248: νῆσαι Ezek 26:15 now νῆσος)')
    # --- grammar-fix pass: grammar lines, relinks, duplicate entries, icons ---
    pt = gcard('Job/13', 11, 'δῖνα')
    check('noun: nominative singular feminine' in pt.lower() and 'future' not in pt.lower(), f'grammar fix: δῖνα (Job 13:11) is N.NSF, not a verb ({pt[:200]!r})')
    pt = gcard('Josh/8', 11, 'ἐξεναντίας')
    check('adverb' in pt.lower() and 'imperfect' not in pt.lower(), f'ἐξεναντίας: entry is Adverb, no verb parse ({pt[:200]!r})')
    pt = gcard('Gen/8', 4, 'μηνὶ')
    check('month' in pt and N('μήν') in N(pt) and 'noun: dative singular masculine' in pt.lower(), f'μηνί relinked to μήν "month" ({pt[:200]!r})')
    pt = gcard('Gen/13', 5, 'βόες')
    check('βοῦς' in pt and 'ox' in pt and 'Boaz' not in pt and 'nominative plural' in pt.lower(), f'βόες (Gen 13:5) relinked to βοῦς, nominative plural ({pt[:200]!r})')
    pt = gcard('Gen/41', 2, 'βόες')
    check('βοῦς' in pt and 'nominative plural feminine' in pt.lower(), f'βόες "cows" (Gen 41:2) feminine ({pt[:200]!r})')
    pt = gcard('Gen/14', 6, 'Φαρὰν')
    check('Paran' in pt and 'Pharao' not in pt, f'Φαρὰν (Gen 14:6) → Paran, not Pharaoh ({pt[:160]!r})')
    LX2 = json.loads(urllib.request.urlopen(B + 'data/lexicon.json').read()); RD = json.loads(urllib.request.urlopen(B + 'data/lexredirect.json').read())
    check('3662' not in LX2 and RD.get('3662') == '16493' and '2993' not in LX2 and RD.get('2993') == '14006' and '1988' not in LX2 and '1988' not in RD, 'duplicates: unused empty entries removed, 48 forwarded (φιλάνθρωπον 3662 → 16493), different words not forwarded')
    check(sum(1 for k in ('3662', '2993', '1988', '9250') if k in LX2) == 0 and len(RD) == 77, f'lexredirect has 77 pairs: 49 earlier merges + 20 NT duplicate headwords (lemma_merge_nt.py) + 8 lemma twins (lemma_twins.py) ({len(RD)})')
    pg.goto(B + '#/search?lex=3662'); pg.wait_for_timeout(900); check('lex=16493' in pg.url, f'old link lex=3662 forwards to 16493 ({pg.url})')
    HD = json.loads(urllib.request.urlopen(B + 'data/lexhide.json').read())
    pg.goto(B + '#/search?q=' + 'ἀποτίκτω'); pg.wait_for_timeout(900)
    hrefs = pg.eval_on_selector_all('.res', 'els => els.map(e => e.getAttribute("href"))')
    check('6318' in HD and 'lex=6318' not in ' '.join(hrefs) and any('lex=' in h for h in hrefs), f'hidden empty entry ἀποτίκτω 6318 not listed in search ({hrefs[:4]})')
    from PIL import Image as _I; import io as _io
    man = json.loads(urllib.request.urlopen(B + 'manifest.webmanifest').read())
    check(man['name'] == 'Gallicantus' and man['short_name'] == 'Gallicantus', 'manifest name and short_name are Gallicantus')
    okic = True
    for ic in man['icons']:
        im = _I.open(_io.BytesIO(urllib.request.urlopen(B + ic['src']).read())).convert('RGBA'); w = int(ic['sizes'].split('x')[0])
        c = im.getpixel((1, 1)); mid = im.getpixel((w // 2, w // 2))
        if im.size != (w, w): okic = False
        if ic['purpose'] == 'maskable' and not (c[3] == 255 and abs(c[0] - 4) < 8 and abs(c[2] - 42) < 10): okic = False
        if ic['purpose'] == 'any' and c[3] != 0: okic = False
    check(okic and len(man['icons']) == 4, 'manifest icons: rooster 192/512 (transparent rounded corners) + maskable 192/512 full-bleed navy #04132a')
    check(urllib.request.urlopen(B + 'favicon.ico').status == 200 and urllib.request.urlopen(B + 'icons/favicon-32.png').status == 200, 'favicon.ico + favicon-32 served')
    pg.goto(B + '#/about'); pg.wait_for_selector('.about-banner'); pg.wait_for_timeout(600)
    bw = pg.evaluate("(() => { const i = document.querySelector('.about-banner'); return [i.naturalWidth, i.getBoundingClientRect().width, document.documentElement.scrollWidth]; })()")
    check(bw[0] == 1024 and bw[1] <= 412 and bw[2] <= 412, f'About banner loads and fits a 412px phone without sideways scroll ({bw})')
    pg.close()
    # --- round 4: middle headwords + merged ἀπολλύω ---
    lx = json.loads(urllib.request.urlopen(B + 'data/lexicon.json').read())
    check(lx['134'][0] == 'φοβέομαι' and lx['234'][0] == 'ἀποκρίνομαι' and lx['49'][0] == 'πορεύομαι' and '596' not in lx and lx['217'][0] == 'ἀπόλλυμι', 'headwords: φοβέομαι, ἀποκρίνομαι, πορεύομαι; ἀπολλύω merged into ἀπόλλυμι')
    fm = json.loads(urllib.request.urlopen(B + 'data/forms/1.json').read())['134']
    check(any(x[0] in ('φοβέω', 'φοβεῖ', 'φοβῶν', 'ἐφόβησεν', 'φοβήσει', 'ἐφόβει') or x[0].startswith('ἐκφοβ') for x in fm.get('f', []) + fm.get('nf', [])) or any(not x[0].endswith(('μαι', 'ται', 'ου', 'σθε', 'θη', 'θης', 'θητε', 'θησαν', 'μενος', 'μενοι', 'σθαι')) for x in fm.get('f', [])), 'φοβέομαι keeps active forms in the same entry')
    pp = br.new_page(viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
    pp.on('pageerror', lambda e: errs.append(str(e)))
    pp.goto(B + '#/Gen/15'); pp.wait_for_selector('#v1 .w'); pp.locator('#v1 .w', has_text='φοβοῦ').first.click(); pp.wait_for_selector('#panel:not([hidden]) .sum'); pp.wait_for_timeout(800)
    if pp.locator('#moreBtn').count(): pp.click('#moreBtn'); pp.wait_for_timeout(900)
    pt = pp.inner_text('#panel'); check('φοβέομαι' in pt and 'phobeomai' in pt and 'frighten' in pt, f'φοβοῦ card: headword φοβέομαι, translit, active sense ({pt[:200]!r})')
    pp.screenshot(path='/workspace/pwa-en-shots/v6_phone_phobeomai_entry.png')
    for q, want in (('phobeo', 'φοβέομαι'), ('φοβεω', 'φοβέομαι'), ('apokrinomai', 'ἀποκρίνομαι'), ('πορευω', 'πορεύομαι'), ('apolluo', 'ἀπόλλυμι'), ('απολλυω', 'ἀπόλλυμι')):
        pp.goto(B + '#/search?q=' + q); pp.wait_for_timeout(700); r0 = pp.locator('.res').first.inner_text() if pp.locator('.res').count() else ''
        check(want in r0, f'search {q!r} → {want} first ({r0[:60]!r})')
    pp.goto(B + '#/search?lex=596'); pp.wait_for_timeout(1000)
    check('lex=217' in pp.url and 'ἀπόλλυμι' in pp.inner_text('#main') and '179' not in pp.inner_text('h1') or ('lex=217' in pp.url and 'ἀπόλλυμι' in pp.inner_text('#main')), f'old link lex=596 redirects to ἀπόλλυμι ({pp.url})')
    h1 = pp.locator('h1').last.inner_text(); check('in the LXX' in h1 and ' 89 in the NT' in h1, f'merged ἀπόλλυμι occurrences include LXX + NT ({h1!r})')
    pp.goto(B + '#/Matt/2/13?lex=596'); pp.wait_for_timeout(1000); check('lex=217' in pp.url and pp.locator('.w.same[data-l="217"]').count() > 0, f'old verse link ?lex=596 redirects ({pp.url})')
    pp.close()
    # --- round 5: forms tables fold capitalisation / final grave / enclitic accent ---
    import glob as _g, unicodedata as _u
    allf = {}
    for fn in _g.glob('data/forms/*.json'):
        for lid, e in json.load(open(fn)).items():
            for part in ('f', 'nf'):
                for r in e.get(part, []): allf.setdefault((lid, part), []).append(r)
    rows31 = allf[('31', 'f')] + allf[('31', 'nf')]; forms31 = {r[0] for r in rows31}
    check(not {'Εἶπεν', 'ΛΕΓΩΝ', 'λέγεί', 'Λέγει'} & forms31 and 'λέγων' in forms31 and 'λέγει' in forms31, 'λέγω forms: no Εἶπεν/ΛΕΓΩΝ/λέγεί/Λέγει rows')
    check(not any(r[0] == 'εἰπὸν' for r in allf.get(('18', 'f'), []) + allf.get(('18', 'nf'), [])), 'εἰπὸν folded into εἰπόν')
    dup = [(k, r[0], r[1]) for k, rs in allf.items() for r in rs if sum(1 for x in rs if x[1] == r[1] and x[0] == r[0]) > 1]
    check(not dup, f'no duplicate form+tag rows in any table ({dup[:3]})')
    check(('61', 'nf') in allf and any(r[0] == 'ἢ' for r in allf[('61', 'nf')]) and any(r[0] == 'ἤ' for r in allf[('61', 'f')]), 'monosyllables keep their written accent (ἤ / ἢ not merged)')
    check(any(r[0] == 'εἰ' for r in allf[('77', 'f')]) and any(r[0] == 'εἶ' for r in allf[('10', 'f')]), 'εἰ / εἶ stay separate')
    vt = json.loads(urllib.request.urlopen(B + 'data/Jer/11.json').read())[0][1]
    check(vt[1][0] == 'ΛΟΓΟΣ', 'verse text unchanged (Jer 11:1 ΛΟΓΟΣ still capitals)')
    pf = br.new_page(viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
    pf.on('pageerror', lambda e: errs.append(str(e)))
    pf.goto(B + '#/Gen/15'); pf.wait_for_selector('#v1 .w'); pf.locator('#v1 .w', has_text='λέγων').first.click(); pf.wait_for_selector('#panel:not([hidden]) .sum'); pf.wait_for_timeout(700)
    if pf.locator('#moreBtn').count(): pf.click('#moreBtn'); pf.wait_for_timeout(500)
    pf.locator('#formsRow summary').first.click(); pf.wait_for_timeout(600)
    pd = pf.text_content('#pdBox'); check('λέγων' in pd and 'ΛΕΓΩΝ' not in pd and 'Εἶπεν' not in pd and 'λέγεί' not in pd, 'λέγω forms table shows merged lowercase rows')
    pf.locator('#formsRow').scroll_into_view_if_needed(); pf.screenshot(path='/workspace/pwa-en-shots/v7_phone_lego_forms_merged.png')
    pf.close()
    # --- round 6: home / contents page ---
    for vp, nm, dark in (({'width': 360, 'height': 780}, 'p360', False), ({'width': 412, 'height': 915}, 'phone', False), ({'width': 412, 'height': 915}, 'p412dark', True), ({'width': 1280, 'height': 900}, 'desktop', False)):
        ctx = br.new_context(viewport=vp, device_scale_factor=1 if nm == 'desktop' else 2); ph = ctx.new_page(); ph.on('pageerror', lambda e: errs.append(str(e)))
        ph.goto(B); ph.wait_for_selector('#toc .tb')
        if dark: ph.evaluate("localStorage.setItem('lxx-theme','dark')"); ph.click('#themeBtn') if ph.evaluate("document.documentElement.dataset.theme") != 'dark' else None
        ph.wait_for_timeout(400)
        check(ph.locator('#contLink').count() == 0, f'{nm} home: first visit has no Continue link')
        secs = ph.eval_on_selector_all('.hsec', 'e => e.map(s => [s.querySelector("h2").textContent, [...s.querySelectorAll(".tb")].map(x => x.dataset.b)])')
        APO = ['1Esdr', '4Esdr', 'Jdt', 'Tob', '1Macc', '2Macc', '3Macc', '4Macc', 'PrMan', 'Wis', 'Sir', 'Bar', 'EpJer', 'Sus', 'Bel']
        check([x[0] for x in secs] == ['Septuagint', 'Apocrypha', 'New Testament'] and secs[1][1] == APO and len(secs[0][1]) == 38 and secs[0][1][:2] == ['Gen', 'Exod'] and secs[0][1][-1] == 'Dan' and len(secs[2][1]) == 27 and secs[2][1][0] == 'Matt', f'{nm} home: 3 sections, Apocrypha in Rahlfs order ({secs[1][1]})')
        check(ph.locator('#toc .apoc').count() == 0, f'{nm} home: no Apocrypha tags on rows')
        check('Prayer of Manasseh (Odes 12)' in ph.inner_text('.tb[data-b=PrMan]'), f'{nm} home: PrMan label')
        gen, obad = ph.inner_text('.tb[data-b=Gen]'), ph.inner_text('.tb[data-b=Obad]')
        check('chapter' not in gen.lower() and 'chapter' not in obad.lower(), f'{nm} home: no chapter counts on Genesis or Obadiah ({gen!r}, {obad!r})')
        toc = ph.inner_text('#toc')
        check(' chapters' not in toc and ' chapter' not in toc, f'{nm} home: no chapter counts in the table of contents')
        check('text in preparation' not in ph.inner_text('.tb[data-b="4Esdr"]'), f'{nm} home: 4 Esdras has its Latin now (no “text in preparation”)')
        ht = ' '.join(ph.inner_text('.htitle').split()); check(ht == 'Greek-Latin Study Bible', f'{nm} home: banner tagline Greek-Latin Study Bible kept under the Gallicantus banner ({ht!r})')
        check(ph.title() == 'Gallicantus' and ' '.join((ph.locator('.brand').text_content() or '').split()) == 'Gallicantus', f'{nm} home: document title and header are Gallicantus')
        ff = ph.eval_on_selector('.htitle', 'e => [getComputedStyle(e).fontFamily, getComputedStyle(e).textAlign]'); check('Gentium' in ff[0] and ff[1] == 'center', f'{nm} home: centred serif title ({ff})')
        ext = ph.evaluate("performance.getEntriesByType('resource').map(r => r.name).filter(u => !u.startsWith(location.origin))"); check(not ext, f'{nm} home: no external requests ({ext[:3]})')
        ow = ph.evaluate('document.documentElement.scrollWidth <= innerWidth'); check(ow, f'{nm} home: no horizontal overflow')
        ph.click('#menuBtn'); ph.wait_for_selector('#books:not([hidden])')
        dgrp = ph.eval_on_selector_all('#bookList .grp', 'e => e.map(s => s.textContent.trim())')
        dids = ph.eval_on_selector_all('#bookList .bk', 'e => e.map(x => x.dataset.b)')
        hids = [b for s in secs for b in s[1]]
        check(dgrp == ['Septuagint', 'Apocrypha', 'New Testament'], f'{nm} drawer: three unnumbered sections {dgrp}')
        check(dids == hids, f'{nm} drawer: book order matches home')
        check(ph.locator('#bookList .apoc').count() == 0, f'{nm} drawer: no Apocrypha tags')
        check(all(g not in ' '.join(dgrp) for g in ('Poetry', 'Wisdom', 'Historical', 'Pentateuch', 'Prophets', 'Law')), f'{nm} drawer: no old sub-headings ({dgrp})')
        check('Prayer of Manasseh (Odes 12)' in ph.inner_text('.bk[data-b=PrMan]'), f'{nm} drawer: PrMan label matches home')
        ph.keyboard.press('Escape'); ph.locator('#books').wait_for(state='hidden')
        if dark: check(ph.evaluate("document.documentElement.dataset.theme") == 'dark', 'dark mode home')
        X = '/workspace/pwa-en-shots/v9_'
        if nm == 'phone':
            ph.screenshot(path=X + 'phone_home_top.png')
            for i, k in ((1, 'apocrypha'), (2, 'nt')): ph.evaluate(f"document.getElementById('hs{i}').scrollIntoView()"); ph.wait_for_timeout(200); ph.screenshot(path=X + f'phone_home_{k}.png')
            ph.evaluate('scrollTo(0,0)')
        elif nm == 'desktop': ph.screenshot(path=X + 'desktop_home.png')
        else: ph.screenshot(path=X + f'{nm}_home_top.png')
        ph.goto(B + '#/Exod/3'); ph.wait_for_selector('.w'); check('Exod' in ph.url, f'{nm}: deep link opens the chapter')
        ph.click('.brand'); ph.wait_for_selector('#contLink'); ct = ph.inner_text('#contLink')
        check('Exodus 3' in ct, f'{nm} home: Continue → Exodus 3 ({ct!r})'); ph.screenshot(path=f'/workspace/pwa-en-shots/v9_{nm}_home_continue.png')
        ph.click('#contLink'); ph.wait_for_selector('.w'); check(ph.url.endswith('#/Exod/3'), f'{nm}: Continue opens the last chapter')
        ph.click('#menuBtn'); ph.click('#homeLink'); ph.wait_for_selector('#toc'); check(ph.locator('#books').is_hidden(), f'{nm}: ☰ → Home works and closes the drawer')
        ph.fill('#hq', 'shepherd'); ph.press('#hq', 'Enter'); ph.wait_for_selector('.res'); check('ποιμ' in ph.inner_text('#results'), f'{nm} home: quick search finds shepherd')
        ctx.close()
    p9.close()
    # ---- votd round: 'Also in' links + hide list + back navigation, Verse of the Day, home banner ----
    import datetime
    LXB = json.loads(urllib.request.urlopen(B + 'data/lexicon.json').read())
    def chap(b, c): return {v[0]: v for v in json.loads(urllib.request.urlopen(B + f'data/{b}/{c}.json').read())}
    pa = br.new_page(viewport={'width': 412, 'height': 915}); pa.on('pageerror', lambda e: errs.append(str(e)))
    pa.goto(B + '#/Gen/1'); pa.wait_for_selector('#v1 .w')
    word(pa, 'οὐρανὸν', 1); pa.wait_for_selector('#ntRow:not([hidden]) a.also')
    links = pa.eval_on_selector_all('#ntRow a.also', 'e => e.map(a => [a.textContent, a.getAttribute("href")])')
    check(len(links) == 3 and all(re.fullmatch(r'#/\w+/\d+/\d+\?lex=\d+', h) for _, h in links), f'also-in: noun οὐρανός has 3 tappable NT passages ({links})')
    good = True
    for t, h in links:
        m = re.fullmatch(r'#/(\w+)/(\d+)/(\d+)\?lex=(\d+)', h); vv = chap(m[1], m[2]).get(m[3])
        good = good and bool(vv) and any(str(x[1]) == m[4] for x in vv[1]) and t == f'{m[1]} {m[2]}:{m[3]}'
    check(good, 'also-in: every link opens a verse that contains the same dictionary word')
    for txt, v, what in (('ἐποίησεν', 1, 'verb'), ('καλὰ', 31, 'adjective'), ('λίαν', 31, 'adverb')):
        word(pa, txt, v); pa.wait_for_timeout(700)
        check(pa.locator('#ntRow a.also').count() > 0, f'also-in kept for a {what} ({txt})')
    pa.goto(B + '#/Gen/2'); pa.wait_for_selector('#v16 .w'); word(pa, 'Ἀδὰμ', 16); pa.wait_for_timeout(700)
    check(pa.locator('#ntRow a.also').count() > 0, 'also-in kept for a name (Ἀδάμ)')
    pa.goto(B + '#/Gen/1'); pa.wait_for_selector('#v1 .w')
    for txt, v, what in (('καὶ', 1, 'conjunction καί'), ('τὸν', 1, 'article ὁ'), ('ἘΝ', 1, 'preposition ἐν'), ('δὲ', 2, 'particle/conjunction δέ')):
        word(pa, txt, v); pa.wait_for_timeout(900)
        check(pa.locator('#ntRow').is_hidden() and pa.locator('#ntRow a.also').count() == 0, f'also-in hidden for the {what}')
    pa.goto(B + '#/John/1'); pa.wait_for_selector('#v1 .w'); word(pa, 'ὁ', 1); pa.wait_for_timeout(900)
    check(pa.locator('#ntRow').is_hidden(), 'also-in hidden for the NT article ὁ (John 1:1)')
    word(pa, 'λόγος', 1); pa.wait_for_selector('#ntRow:not([hidden]) a.also')
    check('John 1:1' not in [a for a in pa.eval_on_selector_all('#ntRow a.also', 'e => e.map(a => a.textContent)')], 'also-in: the current verse is not linked to itself')
    # back navigation: same chapter, same scroll position, same card
    pa.goto(B + '#/Gen/1'); pa.wait_for_selector('#v20 .w'); pa.locator('#v20').scroll_into_view_if_needed(); pa.evaluate('scrollBy(0, 200)')
    word(pa, 'οὐρανοῦ', 20); y0 = pa.evaluate('scrollY'); hl0 = pa.evaluate('history.length')
    pa.wait_for_selector('#ntRow:not([hidden]) a.also'); href = pa.get_attribute('#ntRow a.also >> nth=0', 'href')
    pa.click('#ntRow a.also >> nth=0'); pa.wait_for_selector('.verse.flash'); pa.wait_for_timeout(400)
    m = re.fullmatch(r'#/(\w+)/(\d+)/(\d+)\?lex=(\d+)', href)
    check(pa.url.endswith(href) and pa.locator(f'#v{m[3]}.flash').count() == 1 and pa.locator(f'#v{m[3]} .w.hit').count() >= 1 and pa.evaluate('history.length') == hl0 + 1,
          f'also-in link opens {m[1]} {m[2]}, scrolls to v{m[3]} and rings the word')
    vb = pa.locator(f'#v{m[3]}').bounding_box(); check(0 <= vb['y'] < 915, f'also-in: target verse is on screen (y={int(vb["y"])})')
    pa.go_back(); pa.wait_for_selector('#panel:not([hidden]) .sum'); pa.wait_for_timeout(500)
    y1 = pa.evaluate('scrollY')
    check(pa.url.endswith('#/Gen/1') and abs(y1 - y0) < 4 and N(pa.inner_text('#panelBody .slem')) == N('οὐρανός') and pa.locator('#v20 .w.sel').count() == 1,
          f'back returns to Gen 1 at the same place (y {y0}→{y1}) with the same word card open')
    pa.go_forward(); pa.wait_for_selector('.verse.flash'); check(pa.url.endswith(href), 'forward goes to the linked passage again')
    pa.close()
    # Daily Verses (replaces Verse of the Day): 5 a day, new set at 4 a.m. local, arrows within the day, Settings switch + languages
    VD = json.loads(urllib.request.urlopen(B + 'data/votd.json').read())
    check(len(VD) == 1830 and len({(x[0], x[1], x[2]) for x in VD}) == 1830 and all(len(x) == 6 for x in VD), f'daily: 1,830 distinct verses = 366 days × 5, no Douay column ({len(VD)})')
    bad = []
    for x in VD:
        vv = chap(x[0], x[1]).get(x[2])
        if not vv or vv[2] != x[4] or ' '.join(t[0] for t in vv[1]) != x[3]: bad.append(x[:3])
    check(not bad, f'daily: every ref resolves to a verse with the same Greek and English ({bad[:3]})')
    NTB = {b['id'] for b in json.loads(urllib.request.urlopen(B + 'data/books.json').read()) if b.get('nt')}
    APB = {'Tob', 'Jdt', '1Macc', '2Macc', '3Macc', '4Macc', 'Wis', 'Sir', 'Bar', 'EpJer', 'Sus', 'Bel', '1Esdr', '4Esdr', 'PrMan'}
    sec = [0, 0, 0]
    for x in VD: sec[2 if x[0] in NTB else 1 if x[0] in APB or (x[0], x[1]) in (('Ps', '151'), ('Dan', '3')) else 0] += 1
    nbk = len({x[0] for x in VD}); topb = max(sum(1 for x in VD if x[0] == b) for b in {x[0] for x in VD})
    check(sec[0] >= 750 and sec[1] >= 150 and sec[2] >= 650 and nbk >= 70 and topb <= 0.15 * len(VD), f'daily: spread Septuagint/Apocrypha/NT = {sec}, {nbk} books, largest book {topb}')
    APPR = [l.rstrip('\n').split('\t')[0] for l in open('build/votd/approved366.tsv', encoding='utf-8')][1:]
    check(len(APPR) == 366 and all(f'{VD[5 * d][0]} {VD[5 * d][1]}:{VD[5 * d][2]}' == APPR[d] for d in range(366)), 'daily: the first verse of each day is the approved verse for that date')
    def votd_on(dt, lang=None, off=False, w=412):
        c = br.new_context(viewport={'width': w, 'height': 915}); pg = c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.clock.install(time=dt)
        if lang: c.add_init_script(f"localStorage.setItem('gc-dvlang','{lang}')")
        if off: c.add_init_script("localStorage.setItem('gc-dv','0')")
        pg.goto(B + '#/'); pg.wait_for_selector('#toc .tb')
        if not off: pg.wait_for_selector('#votd:not([hidden])')
        return c, pg
    cum = [0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]
    for dt in (datetime.datetime(2027, 1, 1, 9), datetime.datetime(2027, 3, 1, 9), datetime.datetime(2028, 2, 29, 9), datetime.datetime(2028, 3, 1, 23), datetime.datetime(2026, 12, 25, 8), datetime.datetime(2026, 11, 15, 20)):
        c, pg = votd_on(dt); i = int(pg.get_attribute('#votd', 'data-i')); want = 5 * (cum[dt.month - 1] + dt.day - 1); x = VD[want]
        c2, pg2 = votd_on(dt); same = pg2.inner_text('#votd') == pg.inner_text('#votd'); c2.close()
        check(i == want and x[3] in pg.inner_text('#votd .vgk') and x[4] in pg.inner_text('#votd .ven') and pg.inner_text('#votd .vref').endswith(f'{x[1]}:{x[2]}') and same,
              f'daily: {dt:%Y-%m-%d %H:%M} → day {want // 5} → {x[0]} {x[1]}:{x[2]} first (deterministic)')
        if dt.month == 1 and dt.day == 1: check(x[:3] == ['Gen', '1', '1'], 'daily: 1 January starts with Genesis 1:1')
        if dt.month == 12 and dt.day == 25: check(x[:3] == ['Luke', '2', '14'], 'daily: 25 December starts with Luke 2:14')
        c.close()
    c, pg = votd_on(datetime.datetime(2027, 1, 2, 3, 30))
    check(pg.get_attribute('#votd', 'data-i') == '0', 'daily: before 4 a.m. (2 Jan 03:30) the 1 January set is still shown')
    c.close()
    c, pg = votd_on(datetime.datetime(2027, 1, 2, 4, 1))
    check(pg.get_attribute('#votd', 'data-i') == '5', 'daily: from 4 a.m. (2 Jan 04:01) the 2 January set is shown')
    c.close()
    c, pg = votd_on(datetime.datetime(2026, 12, 31, 12))
    check(int(pg.get_attribute('#votd', 'data-i')) == 1825 and pg.inner_text('#votd .vcount') == '1/5', 'daily: 31 December is the last set (verses 1825-1829), verse 1 of 5')
    seen = []
    for k in range(5): seen.append(pg.get_attribute('#votd', 'data-i')); pg.click('#votdNext')
    check(seen == ['1825', '1826', '1827', '1828', '1829'] and pg.get_attribute('#votd', 'data-i') == '1825', f'daily: › flips through the five verses of the day and wraps ({seen})')
    pg.click('#votdPrev'); check(pg.get_attribute('#votd', 'data-i') == '1829' and pg.inner_text('#votd .vcount') == '5/5', 'daily: ‹ from the first verse goes to the fifth')
    hd = pg.eval_on_selector('#votd', 'e => [e.compareDocumentPosition(document.getElementById("hsearch")) & 4, getComputedStyle(e).display]')
    check(hd[0] == 4, 'daily: card sits above search (and above Continue when present)')
    vt = pg.inner_text('#votd')
    check('daily verses' in vt.lower() and not any(w in vt.lower() for w in ('verse of the day', 'today')) and pg.locator('#votd .vla').count() == 0, 'daily: labelled Daily Verses, no today marker, no Latin by default (Greek + English)')
    x = VD[1829]; pg.click('#votd .vbody'); pg.wait_for_selector('.verse.flash'); check(pg.url.endswith(f'#/{x[0]}/{x[1]}/{x[2]}'), f'daily: tap opens {x[0]} {x[1]} at v{x[2]}')
    pg.go_back(); pg.wait_for_selector('#votd:not([hidden])'); check(pg.url.endswith('#/') or pg.url.endswith('#'), 'daily: back returns to the home page')
    c.close()
    # stale-verse bug: the set and the arrow position follow the clock (4 a.m. rollover while open; on return to the screen)
    c, pg = votd_on(datetime.datetime(2027, 1, 1, 3, 58)); pg.click('#votdNext'); pg.click('#votdNext')
    check(pg.get_attribute('#votd', 'data-i') == '1827', 'daily: 1 Jan 03:58 shows the 31 Dec set (arrows moved to verse 3)')
    pg.clock.run_for(3 * 60 * 1000); pg.wait_for_timeout(200)
    check(pg.get_attribute('#votd', 'data-i') == '0', f'daily: at 4 a.m. the open home page moves to the 1 January set and resets the arrows ({pg.get_attribute("#votd", "data-i")})')
    pg.clock.pause_at(datetime.datetime(2027, 1, 5, 9)); pg.evaluate("document.dispatchEvent(new Event('visibilitychange'))"); pg.wait_for_timeout(200)
    check(pg.get_attribute('#votd', 'data-i') == '20', f'daily: coming back to the screen days later recomputes the set (visibilitychange → 5 Jan) ({pg.get_attribute("#votd", "data-i")})')
    c.close()
    c, pg = votd_on(datetime.datetime(2027, 1, 2, 12), lang='gk'); x = VD[5]
    check(pg.locator('#votd .ven').count() == 0 and pg.locator('#votd .vla').count() == 0 and x[3] in pg.inner_text('#votd .vgk'), 'daily: Greek only setting')
    c.close()
    c, pg = votd_on(datetime.datetime(2027, 1, 2, 12), lang='gkenla'); x = VD[5]
    check(x[5] and x[5][:20] in pg.inner_text('#votd .vla') and x[4][:20] in pg.inner_text('#votd .ven') and pg.locator('#votd .vdr').count() == 0, f'daily: Greek + English + Latin setting, no Douay line ({x[0]} {x[1]}:{x[2]})')
    c.close()
    c, pg = votd_on(datetime.datetime(2027, 1, 2, 12), off=True); pg.wait_for_timeout(500)
    check(pg.locator('#votd').is_hidden(), 'daily: switched off in Settings → no card on home')
    c.close()
    # Settings page: switch + language toggles drive the home card; offline controls live here
    c = br.new_context(viewport={'width': 412, 'height': 915}); pg = c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.clock.install(time='2026-01-01T12:00:00')   # fixed date: the Latin check needs a day whose first verse has Vulgate Latin (not every verse does, e.g. Jer 1:5 on 27 Nov)
    pg.goto(B + '#/Gen/1'); pg.wait_for_selector('.w'); pg.click('#menuBtn'); pg.click('#setLink'); pg.wait_for_selector('.settings')
    check(pg.url.endswith('#/settings') and pg.locator('#books').is_hidden() and pg.locator('#dvOn').is_checked() and pg.locator('input[name=dvlang]').count() == 3 and pg.locator('input[name=dvlang][value=gken]').is_checked(),
          'settings: opened from the side menu; Daily Verses on, languages Greek / Greek + English / Greek + English + Latin (default Greek + English)')
    labs = pg.eval_on_selector_all('.sopt span', 'e => e.map(x => x.textContent)'); check(labs == ['Greek', 'Greek + English', 'Greek + English + Latin'], f'settings: language labels {labs}')
    check(pg.locator('#setDv .sw').count() == 1 and pg.locator('.settings #offline').count() == 1 and pg.locator('#books #offline').count() == 0, 'settings: on/off switch next to the language toggles; offline controls moved here from the side menu')
    pg.click('.sopt:has(input[value=gkenla])'); pg.goto(B + '#/'); pg.wait_for_selector('#votd:not([hidden]) .vla'); check(pg.locator('#votd .vla').count() == 1, 'settings: Greek + English + Latin shows Latin on the home card')
    pg.goto(B + '#/settings'); pg.wait_for_selector('#dvOn', state='attached'); pg.click('#setDv .sw'); pg.goto(B + '#/'); pg.wait_for_selector('#toc .tb'); pg.wait_for_timeout(400)
    check(pg.locator('#votd').is_hidden(), 'settings: switching Daily Verses off hides the card')
    pg.goto(B + '#/settings'); pg.wait_for_selector('#dvOn', state='attached'); pg.click('#setDv .sw'); pg.goto(B + '#/'); pg.wait_for_selector('#votd:not([hidden])'); check(True, 'settings: switching it on again brings the card back')
    c.close()
    # Bookmarks: built-ins, side-menu list + home link, long-press to save a range, opens at the verse with the range highlighted in the saved view
    c = br.new_context(viewport={'width': 412, 'height': 915}, has_touch=True); pg = c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(B + '#/'); pg.wait_for_selector('#toc .tb')
    check(pg.locator('#bmHome').count() == 1 and '2 saved' in pg.inner_text('#bmHome'), 'bookmarks: home link (two built-ins)')
    pg.click('#menuBtn'); names = pg.eval_on_selector_all('#bmList .bmn', 'e => e.map(x => x.textContent)')
    check(names == ['The Lord’s Prayer', 'Psalm 23 (22)'], f'bookmarks: built-ins in the side menu ({names})')
    pg.click('#bmList .bmo[data-bm="lords-prayer"]'); pg.wait_for_selector('.verse.bmhl')
    hl = pg.eval_on_selector_all('.verse.bmhl', 'e => e.map(x => x.id)')
    check(pg.url.endswith('#/Matt/6/9?to=13') and hl == ['v9', 'v10', 'v11', 'v12', 'v13'] and pg.locator('#books').is_hidden(), f'bookmarks: the Lord’s Prayer opens Matthew 6 at v9 with 9–13 highlighted ({hl})')
    top = pg.eval_on_selector('#v9', 'e => e.getBoundingClientRect().top'); check(0 < top < 400, f'bookmarks: scrolled to the first verse ({top:.0f}px)')
    pg.goto(B + '#/bookmarks'); pg.wait_for_selector('.bmpage'); pg.click('.bmpage .bmo[data-bm="psalm-23"]'); pg.wait_for_selector('.verse.bmhl')
    check(pg.url.endswith('#/Ps/22/1?to=6') and pg.locator('.verse.bmhl').count() == 6 and 'ποιμαίνει' in pg.inner_text('#v1'), 'bookmarks: Psalm 23 (22) opens LXX Ps 22:1–6')
    pg.goto(B + '#/Gen/1'); pg.wait_for_selector('#v3 .w'); pg.locator('.modebar [data-mode="greek"]').first.click(); pg.wait_for_timeout(300)
    bx = pg.locator('#v3').bounding_box(); pg.mouse.move(bx['x'] + 30, bx['y'] + 12); pg.mouse.down(); pg.wait_for_timeout(800); pg.mouse.up()
    pg.wait_for_selector('#panel:not([hidden]) .bmsheet'); check('Genesis 1:3' in pg.inner_text('#bmRef') and pg.locator('#v3.bmsel').count() == 1, 'bookmarks: long-press verse 3 opens the bookmark sheet')
    pg.select_option('#bmTo', '5'); pg.fill('#bmName', 'Light'); check(pg.locator('.verse.bmsel').count() == 3, 'bookmarks: choosing “through verse 5” marks 3–5')
    pg.screenshot(path='/workspace/lxx-latin/batch-build/shots/t_bookmark_sheet.png'); pg.click('#bmSaveBtn'); pg.wait_for_timeout(200)
    a = pg.evaluate("JSON.parse(localStorage.getItem('gc-bm'))"); m = a[-1]
    check(len(a) == 3 and m['name'] == 'Light' and m['b'] == 'Gen' and m['ch'] == '1' and m['v1'] == 3 and m['v2'] == 5 and m['mode'] == 'greek' and pg.locator('#panel').is_hidden(), f'bookmarks: saved with name, range and view ({m})')
    pg.locator('.modebar [data-mode="latin-en"]').first.click(); pg.wait_for_timeout(300); pg.goto(B + '#/Exod/1'); pg.wait_for_selector('.verse')
    pg.click('#menuBtn'); pg.click(f'#bmList .bmo[data-bm="{m["id"]}"]'); pg.wait_for_selector('.verse.bmhl')
    check(pg.url.endswith('#/Gen/1/3?to=5') and pg.evaluate("localStorage.getItem('lxx-mode')") == 'greek' and pg.locator('.verse.bmhl').count() == 3 and pg.locator('.lverse').count() == 0, 'bookmarks: opens in the view it was saved in (Greek), verses 3–5 highlighted')
    pg.click('#menuBtn'); pg.click('#bmList .bmdel[data-del="lords-prayer"]'); pg.wait_for_timeout(200)
    names = pg.eval_on_selector_all('#bmList .bmn', 'e => e.map(x => x.textContent)'); check(names == ['Psalm 23 (22)', 'Light'], f'bookmarks: a built-in can be deleted like any other ({names})')
    pg.keyboard.press('Escape'); pg.goto(B + '#/'); pg.wait_for_selector('#bmHome'); check('2 saved' in pg.inner_text('#bmHome'), 'bookmarks: home link count follows')
    pg.goto(B + '#/Gen/1'); pg.wait_for_selector('#v1 .w'); pg.locator('#v1 .w').first.click(); pg.wait_for_selector('#panel:not([hidden]) .sum'); check(pg.locator('.bmsheet').count() == 0, 'bookmarks: a plain tap still opens the word card')
    c.close()
    # shorter side menu: folded sections, current book's section open, settings/about links
    c = br.new_context(viewport={'width': 412, 'height': 915}); pg = c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(B + '#/'); pg.wait_for_selector('#toc .tb'); pg.click('#menuBtn'); pg.wait_for_timeout(200)
    sh = pg.evaluate("Math.round(document.getElementById('bookList').getBoundingClientRect().bottom)")
    check(pg.locator('#bookList .gbody:not([hidden])').count() == 0 and sh < 915 and pg.locator('#books .dnav a').count() == 3, f'side menu: sections folded on home; whole menu fits one screen ({sh}px)')
    pg.click('#bookList .grp[data-g="2"]'); check(pg.locator('#bookList .gbody[data-g="2"]').is_visible() and pg.get_attribute('#bookList .grp[data-g="2"]', 'aria-expanded') == 'true', 'side menu: tapping a section opens it')
    pg.keyboard.press('Escape'); pg.goto(B + '#/Isa/1'); pg.wait_for_selector('.w'); pg.click('#menuBtn'); pg.wait_for_timeout(200)
    check(pg.locator('#bookList .gbody[data-g="0"]').is_visible() and pg.locator('.bk.cur[data-b="Isa"]').is_visible(), 'side menu: the current book’s section opens with the menu')
    c.close()
    # etymology cleanup: no 'Etymology tree' ancestor lists glued into the text
    ET = {}
    for i in range(0, 200):
        try: ET.update(json.loads(urllib.request.urlopen(B + f'data/etym/{i}.json').read()))
        except Exception: pass
    badet = [k for k, v in ET.items() if 'Etymology tree' in v['t'] or 'PIE word' in v['t'] or '▲' in v['t'] or re.search(r'(Proto-[\w-]+ \*[^\s,;:.()]+ ){2}', v['t'])]
    check(len(ET) > 4000 and not badet, f'etymology: {len(ET)} entries, none with tree residue ({badet[:5]})')
    pg = br.new_page(viewport={'width': 412, 'height': 915}); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(B + '#/Gen/1'); pg.wait_for_selector('#v1 .w'); word(pg, 'Θεὸς', 1); pg.wait_for_selector('#etyRow:not([hidden])'); et = pg.inner_text('#etyRow')
    check('From Proto-Hellenic *tʰehós' in et and 'Etymology tree' not in et and 'Proto-Indo-European *-s Proto' not in et, f'etymology: θεός reads “From Proto-Hellenic *tʰehós …” ({et[:70]!r})')
    pg.evaluate("document.getElementById('etyRow').scrollIntoView({block:'center'})"); pg.wait_for_timeout(200); pg.screenshot(path='/workspace/lxx-latin/batch-build/shots/t_theos_etymology.png')
    pg.close()
    # Android back: the native callback walks the WebView history (static check; no emulator on this machine)
    ma = open('build/android/MainActivity.java', encoding='utf-8').read()
    check('OnBackPressedCallback' in ma and 'canGoBack()' in ma and 'goBack()' in ma, 'android: MainActivity back callback walks the WebView history (copy in build/android)')
    # home banner (replaces the big text title)
    for theme in ('light', 'dark'):
        c = br.new_context(viewport={'width': 412, 'height': 915}); c.add_init_script(f"localStorage.setItem('lxx-theme','{theme}')"); pg = c.new_page()
        pg.goto(B + '#/'); pg.wait_for_selector('.hbanner img'); pg.wait_for_function("document.querySelector('.hbanner img').complete")
        bi = pg.eval_on_selector('.hbanner img', 'i => [i.naturalWidth, i.getBoundingClientRect().width, i.getBoundingClientRect().right, i.alt, getComputedStyle(i.parentNode).backgroundColor, getComputedStyle(i.parentNode).borderTopLeftRadius]')
        check(bi[0] == 1086 and 300 <= bi[1] <= 400 and bi[2] <= 412 and 'Gallicantus' in bi[3] and 'rooster' in bi[3] and bi[4] == 'rgb(5, 20, 41)' and bi[5] != '0px',
              f'{theme} home: Gallicantus banner on a rounded navy card, fits 412px, alt text ({bi[:3]}, {bi[4]})')
        sub = pg.eval_on_selector('.hbanner .hsub', 'e => [e.textContent, parseFloat(getComputedStyle(e).fontSize), e.getBoundingClientRect().width]')
        check(sub[0] == 'Greek-Latin Study Bible' and sub[1] >= 15, f'{theme} home: app name as real text under the banner ({sub})')
        check(pg.locator('h1.htitle').count() == 1 and pg.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'{theme} home: one h1, no sideways scroll')
        c.close()
    # ---- Gallicantus round: name, top bar, drawer caps, 4 Esdras tag, LICENSE/NOTICE/README titles, descendants ----
    pg = br.new_page(viewport={'width': 412, 'height': 915}); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(B + '#/Gen/1'); pg.wait_for_selector('#v1 .w')
    bb = pg.eval_on_selector('.brand', 'e => [e.innerText, e.scrollWidth <= e.clientWidth + 1, e.getBoundingClientRect().right <= innerWidth, getComputedStyle(e).display]')
    check(bb[0] == 'Gallicantus' and bb[1] and bb[2] and bb[3] != 'none', f'412px top bar shows the full name Gallicantus ({bb})')
    pg.click('#menuBtn'); pg.wait_for_selector('#books:not([hidden])')
    gs = pg.eval_on_selector_all('#bookList .grp', 'e => e.map(g => [g.innerText, getComputedStyle(g).textTransform])')
    check([g[0] for g in gs] == ['Septuagint', 'Apocrypha', 'New Testament'] and all(g[1] == 'none' for g in gs), f'drawer section labels use the home page capitalization, no all-caps ({gs})')
    e4 = pg.eval_on_selector('.bk[data-b="4Esdr"]', 'e => [e.innerText.trim(), e.querySelectorAll(".bl").length]')
    check(e4 == ['4 Esdras', 0] and pg.locator('#bookList .bl').count() == 0, f'drawer: no LATIN tag on 4 Esdras ({e4})')
    pg.evaluate("document.getElementById('books').scrollTop = 400"); pg.wait_for_timeout(150)
    hd = pg.evaluate("(() => { const h = document.querySelector('.drawer-head').getBoundingClientRect(), d = document.getElementById('books').getBoundingClientRect(); return [h.top - d.top, parseFloat(getComputedStyle(document.getElementById('books')).paddingTop)]; })()")
    check(abs(hd[0]) < 1 and hd[1] == 0, f'drawer: sticky Books bar sits flush at the top, nothing peeks above it ({hd})')
    pg.keyboard.press('Escape')
    pg.goto(B + '#/'); pg.wait_for_selector('.tb[data-b="4Esdr"]'); check(pg.locator('.tb[data-b="4Esdr"] .bl').count() == 0 and pg.locator('#toc .bl').count() == 0, 'home: no LATIN tag on 4 Esdras')
    for f, want in (('LICENSE', 'Gallicantus (Greek-Latin Study Bible): licences'), ('NOTICE', 'Gallicantus (Greek-Latin Study Bible): third-party material and licences'), ('README.md', '# Gallicantus (Greek-Latin Study Bible)')):
        t = open(f, encoding='utf-8').read(); check(t.splitlines()[0] == want and 'Static Rooster Media' in (t if f != 'README.md' else open('LICENSE', encoding='utf-8').read()), f'{f}: title “{want}”, copyright holder Static Rooster Media')
    # descendants: exact dictionary form only; no list → no row at all
    DS = {}
    for i in range(0, 200):
        try: DS.update(json.loads(urllib.request.urlopen(B + f'data/desc/{i}.json').read()))
        except Exception: pass
    check(len(DS) > 3000, f'descendants: {len(DS)} Greek entries have a Wiktionary list')
    pg.goto(B + '#/Gen/1'); pg.wait_for_selector('#v1 .w')
    word(pg, 'Θεὸς', 1); pg.wait_for_selector('#descRow:not([hidden])'); t = pg.inner_text('#descRow')
    check(t.startswith('DESCENDANTS') or t.lower().startswith('descendants'), f'θεός: Descendants row on the More view ({t[:60]!r})')
    check('Greek θεός' in N(t) and 'Wiktionary · CC BY-SA 4.0' in t and pg.locator('#descRow .dmore').is_hidden(), 'θεός: compact list with the Wiktionary CC BY-SA credit, long list folded')
    pg.click('#descRow .dtog'); check(pg.locator('#descRow .dmore').is_visible() and pg.get_attribute('#descRow .dtog', 'aria-expanded') == 'true', 'θεός: toggle shows the rest of the list')
    pg.click('#descRow .dtog'); check(pg.locator('#descRow .dmore').is_hidden(), 'θεός: toggle folds it again')
    word(pg, 'ἀκατασκεύαστος', 2); pg.wait_for_timeout(900)
    check(pg.locator('#descRow').is_hidden() and 'Descendants' not in pg.inner_text('#panelBody') and 'DESCENDANTS' not in pg.inner_text('#panelBody'), 'ἀκατασκεύαστος (no list): no Descendants section at all')
    pg.goto(B + '#/Gen/1'); pg.wait_for_selector('#v3 .w'); word(pg, 'γενηθήτω', 3); pg.wait_for_timeout(900)
    check(N(pg.inner_text('#panelBody .slem')) == N('γίνομαι') and pg.locator('#descRow').is_hidden() and '30' not in DS, 'γίνομαι: no list borrowed from the related form γίγνομαι')
    # regression: one dictionary word split over two TAGNT numbers must not hide its NT/LXX hits (ἅγιος showed 11 hits, all Hebrews, 0 LXX)
    import re as _re
    for lem, lid, lxx_rng, nt_rng in (('ἅγιος', 75, (700, 850), (225, 240)), ('θεός', 20, (3500, 3800), (1300, 1330)), ('κύριος', 7, (7800, 8300), (700, 730)), ('ἐγώ', 6, (11000, 12000), (2500, 2650))):
        pg.goto(B + '#/search?q=' + lem); pg.wait_for_selector('#results .res'); pg.wait_for_timeout(200)
        rows = [t for t in pg.locator('#results .res').all_inner_texts() if N(t.split()[0]) == N(lem)]
        m = _re.search(r'(\d+)× LXX · (\d+)× NT', rows[0] if rows else '')
        check(len(rows) == 1 and m and lxx_rng[0] <= int(m.group(1)) <= lxx_rng[1] and nt_rng[0] <= int(m.group(2)) <= nt_rng[1], f'search {lem}: one {lem} row with LXX and NT counts in range ({[r[:60] for r in rows]})')
        pg.goto(B + '#/search?lex=%d' % lid); pg.wait_for_selector('#results h1'); h1 = pg.inner_text('#results h1')
        m = _re.search(r'\((\d+) in the LXX, (\d+) in the NT\)', h1); grps = pg.locator('#results .grp').count()
        check(m and lxx_rng[0] <= int(m.group(1)) <= lxx_rng[1] and nt_rng[0] <= int(m.group(2)) <= nt_rng[1] and grps > 20, f'{lem} occurrences: LXX and NT verses listed ({h1[-60:]!r}, {grps} books)')
    pg.goto(B + '#/search?lex=11330'); pg.wait_for_selector('#results h1'); pg.wait_for_timeout(200)
    check('lex=75' in pg.evaluate('location.hash') and '(771 in the LXX' in pg.inner_text('#results h1'), f'old ἅγιος (G0039) link redirects to the merged entry ({pg.evaluate("location.hash")})')
    pg.goto(B + '#/Heb/9'); pg.wait_for_selector('#v2 .w'); word(pg, 'Ἅγια', 2); pg.wait_for_timeout(600)
    check(N(pg.inner_text('#panelBody .slem')) == N('ἅγιος') and 'LXX' in pg.inner_text('#freqChip') + pg.inner_text('#panelBody'), 'Heb 9:2 Ἅγια: card shows the one ἅγιος entry (LXX + NT)')
    LX = json.loads(urllib.request.urlopen(B + 'data/lexicon.json').read()); CO = json.loads(urllib.request.urlopen(B + 'data/counts.json').read()); NC = json.loads(urllib.request.urlopen(B + 'data/ntcounts.json').read())
    byh = {}
    for k, v in LX.items(): byh.setdefault(N(v[0]), []).append(k)
    split = sorted(h for h, ks in byh.items() if len(ks) > 1 and any(not CO.get(k) and NC.get(k) for k in ks))
    REVIEWED = sorted(N(x) for x in ('σύνειμι',))   # true homograph kept apart with distinct glosses; ἄπειμι and βάτος twins now have LXX tokens too (lemma_twins.py round 2)
    check(split == REVIEWED, f'no new NT-only duplicate headwords; the remaining {len(split)} are reviewed homographs ({split})')
    # ---- lemma twins (Greek Maestro's calls, build/tools/lemma_twins.py) ----
    RD = json.loads(urllib.request.urlopen(B + 'data/lexredirect.json').read())
    def srow(q, lid):   # the search row for entry lid, counts stripped
        pg.goto(B + '#/search?q=' + urllib.parse.quote(q)); pg.wait_for_selector('#results .res'); pg.wait_for_timeout(150)
        r = pg.locator(f'#results a.res[href="#/search?lex={lid}"]')
        return _re.sub(r'\s*·\s*[\d,]+× (LXX|NT)|\s*·\s*(LXX|NT) only', '', r.first.inner_text()).strip() if r.count() == 1 else None
    TW = (('μή', '25', 'μήτι', '10058'), ('μακρός', '642', 'μακράν', '10068'), ('χράομαι', '928', 'χράω', '10376'), ('ἀνάθεμα', '1695', 'ἀνάθημα', '4513'),
          ('ἄπειμι', '2818', 'ἄπειμι', '10642'), ('σύνειμι', '2291', 'σύνειμι', '10359'), ('βάτος', '2872', 'βάτος', '10394'), ('εἴκω', '5610', 'ἔοικα', '5369'), ('οἶδα', '1168', 'εἶδον', '53'))
    for qa, ia, qb, ib in TW:
        ra, rb = srow(qa, ia), srow(qb, ib)
        check(ra and rb and ra != rb and ra.split('\n')[-1] != rb.split('\n')[-1], f'twins {qa}/{qb}: distinct search rows and glosses ({ra!r} | {rb!r})')
    pg.goto(B + '#/search?lex=10394'); pg.wait_for_selector('#results h1')
    check('bath' in pg.inner_text('#results h1') and 'thornbush' not in pg.inner_text('#results h1'), 'βάτος (Luke 16:6) occurrence page is labelled bath, not thornbush')
    pg.goto(B + '#/search?lex=10642'); pg.wait_for_selector('#results h1')
    check('go away' in pg.inner_text('#results h1') and '17:10' in pg.inner_text('#results'), 'ἄπειμι go away (Acts 17:10) occurrence page labelled')
    # merges: one entry each, old ids forward
    for q, lid in (('ἅπτω', '465'), ('ἔπω', '10054')):
        pg.goto(B + '#/search?q=' + q); pg.wait_for_selector('#results .res'); pg.wait_for_timeout(150)
        rows = [t for t in pg.locator('#results .res').all_inner_texts() if N(t.split()[0]) == N(q)]
        check(len(rows) == 1 and pg.locator(f'#results a.res[href="#/search?lex={lid}"]').count() == 1, f'merge: one {q} row ({rows})')
    check('kindle' in LX[('465')][1] and 'touch' in LX['465'][1] and NC.get('465', 0) >= 35 and CO.get('465', 0) > 100, f'ἅπτω: one entry touch/kindle, LXX + NT ({LX["465"][1]}, {CO.get("465")}, {NC.get("465")})')
    for old, new in (('10060', '465'), ('9993', '10054'), ('9997', '10054'), ('10044', '1168'), ('10749', '1168'), ('11353', '5369'), ('10420', '4513'), ('16507', '928')):
        check(old not in LX and RD.get(old) == new, f'merge: lexicon {old} gone, redirect {old} → {new}')
    for old, new in (('9997', '10054'), ('10060', '465')):
        pg.goto(B + '#/search?lex=' + old); pg.wait_for_timeout(900); check('lex=' + new in pg.url, f'old link lex={old} forwards to {new} ({pg.url})')
    # splits: only the one token moves
    for bk, ch, v, lid, hw, frm in (('1Cor', 10, 11, '10962', 'τυπικῶς', 'τυπικῶς'), ('Acts', 21, 6, '10720', 'ἀπασπάζομαι', None)):
        V = [x for x in json.loads(urllib.request.urlopen(B + f'data/{bk}/{ch}.json').read()) if str(x[0]) == str(v)][0]
        tok = [w for w in V[1] if str(w[1]) == lid]
        check(len(tok) == 1 and NC.get(lid) == 1 and not CO.get(lid), f'split: {hw} has exactly its {bk} {ch}:{v} token ({tok}, NT {NC.get(lid)})')
        pg.goto(B + f'#/{bk}/{ch}'); pg.wait_for_selector(f'#v{v} .w'); word(pg, tok[0][0] if tok else frm, v); pg.wait_for_timeout(500)
        check(N(pg.inner_text('#panelBody .slem')) == N(hw), f'{bk} {ch}:{v}: card shows {hw} ({pg.inner_text("#panelBody .slem")!r})')
    check(LX['10962'][2] == 'Adverb' and 'example' in LX['10962'][1] and 'farewell' in LX['10720'][1], 'split entries: τυπικῶς adverb “as an example”, ἀπασπάζομαι “say farewell”')
    def forms(lid): return json.loads(urllib.request.urlopen(B + f'data/forms/{int(lid) // 100}.json').read()).get(lid, {})
    check(not any(N(f[0]).startswith(N('τυπικ')) for f in forms('4449').get('nf', [])) and N(LX['4449'][0]) == N('τύπος'), 'τύπος no longer lists τυπικῶς')
    check(not any(N(f[0]).startswith(N('ἀπησπα')) for f in forms('3174').get('nf', [])) and N(LX['3174'][0]) == N('ἀποσπάω'), 'ἀποσπάω no longer lists ἀπησπασάμεθα')
    # εἶδον / οἶδα: perfect-system forms sit under οἶδα 'know', aorist under εἶδον 'see' (cross-linked to ὁράω)
    MO = json.loads(urllib.request.urlopen(B + 'data/morph.json').read())
    ei = forms('53')
    check(not any(_re.search(r'perfect|future', str(MO[f[1]][1] if isinstance(MO[f[1]], list) else MO[f[1]]), _re.I) for f in ei.get('f', []) + ei.get('nf', [])), 'εἶδον: no perfect/pluperfect/future forms left (they are οἶδα)')
    for lid, hw, xl, xid in (('53', 'εἶδον', 'ὁράω', '112'), ('10054', 'ἔπω', 'λέγω', '31'), ('10058', 'μήτι', 'μή', '25'), ('10068', 'μακράν', 'μακρός', '642')):
        pg.goto(B + '#/search?lex=' + lid); pg.wait_for_selector('#results h1')
        a = pg.locator(f'#results h1 a.xref[href="#/search?lex={xid}"]')
        check(a.count() == 1 and N(a.inner_text()) == N(xl), f'{hw} occurrence page: “see also {xl}” link')
    pg.goto(B + '#/Gen/12'); pg.wait_for_selector('#v1 .w')
    G = [x for x in json.loads(urllib.request.urlopen(B + 'data/Gen/12.json').read())]
    hit = [(x[0], w[0]) for x in G for w in x[1] if str(w[1]) == '53'][:1]
    if hit:
        word(pg, hit[0][1], hit[0][0]); pg.wait_for_timeout(500)
        check(N(pg.inner_text('#panelBody .slem')) == N('εἶδον') and pg.locator('#panelBody .sxref a.xref[href="#/search?lex=112"]').count() == 1, f'Gen 12:{hit[0][0]} {hit[0][1]}: card shows εἶδον with See also ὁράω')
    else: check(False, 'Gen 12: an εἶδον token to test the card cross-link')
    # ---- round 2: Greek Maestro's rulings on build/lemma_twins_review.tsv (lemma_twins.py RULINGS; log in build/lemma_twins_rulings.tsv) ----
    LX = json.loads(urllib.request.urlopen(B + 'data/lexicon.json').read()); CO = json.loads(urllib.request.urlopen(B + 'data/counts.json').read()); NC = json.loads(urllib.request.urlopen(B + 'data/ntcounts.json').read())
    def fl(lid, side='f'): return [N(f[0]) for f in forms(lid).get(side, [])]
    def tok_lex(bk, ch, v, form):
        V = [x for x in json.loads(urllib.request.urlopen(B + f'data/{bk}/{ch}.json').read()) if str(x[0]) == str(v)][0]
        return [str(w[1]) for w in V[1] if N(w[0]) == N(form)]
    def card(bk, ch, v, form):
        pg.goto(B + f'#/{bk}/{ch}'); pg.wait_for_selector(f'#v{v} .w')   # no word(): particles have no form tabs
        pg.locator(f'#v{v} .w', has_text=form).first.click(); pg.wait_for_selector('#panel:not([hidden]) .slem'); pg.wait_for_timeout(500)
        return N(pg.inner_text('#panelBody .slem')), pg.inner_text('#panelBody .sdef')
    for bk, ch, v, form, lid, hw, gl in (('Gen', 20, 9, 'μήτι', '10058', 'μήτι', 'question particle'), ('Gen', 44, 4, 'μακράν', '10068', 'μακράν', 'far away'),
                                          ('Exod', 11, 3, 'ἔχρησαν', '10376', 'χράω', 'lend'), ('2Macc', 12, 1, 'ἀπῄει', '10642', 'ἄπειμι', 'go away'),
                                          ('Ps', 13, 2, 'συνιὼν', '606', 'συνίημι', ''), ('2Esdr', 7, 22, 'βατῶν', '10394', 'βάτος', 'bath')):
        tl = tok_lex(bk, ch, v, form); hc = card(bk, ch, v, form)
        check(tl and all(x == lid for x in tl) and hc[0] == N(hw) and gl in hc[1], f'ruling: {bk} {ch}:{v} {form} is filed under {hw} {lid} ({tl}, card {hc[0]} “{hc[1][:50]}”)')
    check(CO.get('10058') == 3 and not any(f.lower().startswith(N('μήτι')) for f in fl('25')), f'1 μήτι: 3 LXX tokens moved off μή ({CO.get("10058")})')
    mk = [f for f in fl('642') if f.lower() in (N('μακράν'), N('μακρὰν'))]
    check(CO.get('10068') == 66 and CO.get('642') == 17 and len(mk) >= 1, f'2 μακράν: 66 adverbial LXX tokens moved; μακρός keeps 17 incl. agreeing μακράν forms ({CO.get("10068")}, {CO.get("642")}, {mk})')
    for bk, ch, v, form, lid in (('Prov', 7, 19, 'μακράν', '642'), ('Luke', 15, 13, 'μακρὰν', '642'), ('1Kgs', 8, 46, 'μακρὰν', '642'), ('Sir', 30, 23, 'μακρὰν', '10068'), ('Num', 9, 10, 'μακρὰν', '10068'), ('Jdt', 3, 2, 'χρῆσαι', '928'), ('Jdt', 3, 3, 'χρῆσαι', '928'), ('4Macc', 13, 13, 'χρήσωμεν', '10376')):
        tl = tok_lex(bk, ch, v, form); check(tl == [lid], f'ruling: {bk} {ch}:{v} {form} → {LX[lid][0]} {lid} ({tl})')
    check(CO.get('10376') == 4 and NC.get('10376') == 1 and not any(f.startswith(N('ἔχρησ')) for f in fl('928')), f'3 χράω lend: 4 LXX + 1 NT; χράομαι keeps no ἔχρησ- forms ({CO.get("10376")}, {NC.get("10376")})')
    check(CO.get('10642') == 4 and NC.get('10642') == 1 and 'depart' in LX['10642'][1] and not any(f.startswith((N('ἀπῄ'), N('ἀπι'))) for f in fl('2818') + fl('2818', 'nf')), f'4 ἄπειμι go away: 4 LXX + Acts 17:10; be-absent entry keeps no εἶμι forms ({CO.get("10642")}, {fl("2818")})')
    check(CO.get('2291') == 4 and not any(f.lower().startswith(N('συνι')) for f in fl('2291')) and CO.get('606') == 100, f'5 συνι- participles moved to συνίημι ({CO.get("2291")}, {CO.get("606")})')
    check(CO.get('10394') == 2 and NC.get('10394') == 1 and CO.get('2872') == 7 and N('βατῶν') not in fl('2872'), f'6 βατῶν → ὁ βάτος bath (2 LXX + Luke 16:6) ({CO.get("10394")}, {CO.get("2872")})')
    NTJ = json.loads(urllib.request.urlopen(B + 'data/nt.json').read())
    check(all(len(v) <= 4 for v in NTJ.values()), f'nt.json: count + at most 3 refs per entry ({[k for k, v in NTJ.items() if len(v) > 4][:5]})')
    # ---- NT English review (build/tools/nt_english_review.py, Greek Maestro's nt_trim_reviewed.tsv): trims, moves, BLANK/HOLD not yet applied ----
    def ven(bk, ch, v):
        pg.goto(B + f'#/{bk}/{ch}'); pg.wait_for_selector('#v1')
        loc = pg.locator(f'#v{v}')
        return loc.locator('.en3').inner_text() if loc.count() and loc.locator('.en3').count() else (None if not loc.count() else '')
    def vjs(bk, ch): return {x[0]: x for x in json.loads(urllib.request.urlopen(B + f'data/{bk}/{ch}.json').read())}
    t = ven('Matt', 6, 13); check(t.endswith('from the evil one.’') and 'Kingdom' not in t, f'Matt 6:13: doxology trimmed ({t!r})')
    t = ven('Luke', 11, 2); check('‘Father, may your name be kept holy. May your Kingdom come.' in t and 'Our Father' not in t and 'will be done' not in t, f'Luke 11:2: shorter prayer ({t!r})')
    t = ven('Luke', 11, 4); check(t.endswith('Bring us not into temptation.’”') and 'deliver' not in t, f'Luke 11:4: “deliver us from the evil one” trimmed ({t!r})')
    t = ven('Mark', 6, 11); check('Sodom' not in t and t.endswith('against them.”'), f'Mark 6:11: Sodom clause trimmed ({t!r})')
    R14, R16 = vjs('Rom', 14), vjs('Rom', 16)
    check(not any(k in R14 for k in ('24', '25', '26')) and R16['25'][2].startswith('Now to him who is able') and R16['27'][2].endswith('forever! Amen.') and R16['25'][1], 'move: Rom 14:24-26 doxology English now under the NA28 Greek of Rom 16:25-27; no empty Rom 14:24-26 rows')
    t = ven('Rom', 16, 26); check(t.startswith('but now is revealed'), f'Rom 16:26 shows its English in the app ({t!r})')
    C13 = vjs('2Cor', 13)
    check('14' not in C13 and C13['12'][2] == 'Greet one another with a holy kiss. All the saints greet you.' and C13['13'][2].startswith('The grace of the Lord Jesus Christ') and not C13['13'][2].endswith('Amen.'), 'move: 2 Cor 13:13 = the grace (no Amen), 13:12 + “All the saints greet you.”, no 13:14')
    J3, R12, R13 = vjs('3John', 1), vjs('Rev', 12), vjs('Rev', 13)
    check(J3['14'][2].endswith('face to face.') and J3['15'][2] == 'Peace be to you. The friends greet you. Greet the friends by name.' and R12['18'][2] == 'Then he stood on the sand of the sea.' and R13['1'][2].startswith('I saw a beast'), 'move: 3 John 1:15 and Rev 12:18 now have their English (ἐστάθη: “he stood”)')
    REMOVED = (('Matt', 17, 21), ('Matt', 18, 11), ('Matt', 23, 14), ('Mark', 7, 16), ('Mark', 9, 44), ('Mark', 9, 46), ('Mark', 11, 26), ('Mark', 15, 28), ('Luke', 23, 17), ('John', 5, 4), ('Acts', 28, 29), ('Rom', 16, 24))
    check(all(str(v) not in vjs(bk, ch) for bk, ch, v in REMOVED), 'BLANK applied (Drake): the 12 WEB-only verses are taken out of the chapter data')
    pg.goto(B + '#/Matt/17'); pg.wait_for_selector('#v22')
    check(pg.locator('#v21').count() == 0 and 'Not in the NA28' not in pg.inner_text('#main') and pg.locator('#v20 .en3').count() == 1 and pg.locator('#v22 .en3').count() == 1, 'Matt 17: v.21 gone with no note and no bare number; vv.20 and 22 intact')
    for bk, ch, v, near in (('Matt', 17, 21, 20), ('John', 5, 4, 3), ('Rom', 16, 24, 23), ('Mark', 9, 44, 43)):
        pg.goto(B + f'#/Gen/1'); pg.wait_for_selector('#v1'); pg.goto(B + f'#/{bk}/{ch}/{v}'); pg.wait_for_selector(f'#v{near}'); pg.wait_for_timeout(500)
        fl = pg.locator('#main .verse.flash')
        check(fl.count() == 1 and fl.first.get_attribute('id') == f'v{near}' and pg.evaluate(f"(() => {{ const r = document.getElementById('v{near}').getBoundingClientRect(); return r.bottom > 0 && r.top < innerHeight; }})()"), f'link to removed {bk} {ch}:{v} lands on the chapter at v.{near} (nearest earlier verse)')
    pg.goto(B + '#/Matt/17'); pg.wait_for_selector('#v22'); pg.locator('text=La+Gk').first.click(); pg.wait_for_timeout(900)
    check(pg.locator('#main .verse').count() > 20 and pg.locator('#v21').count() == 0, f'Latin + Greek mode still renders Matt 17 without v.21 ({pg.locator("#main .verse").count()} rows)')
    pg.locator('text=Gk+En').first.click(); pg.wait_for_timeout(400)
    t = ven('John', 8, 7); check(t == 'But when they continued asking him, he looked up and said to them, “He who is without sin among you, let him throw the first stone at her.”', f'John 8:7 kept as WEB (no review row; HOLD rows applied per final_english) ({t[:40]!r})')
    # Drake: Greek we use gets its English, no brackets or notes (Mark 16:8-20, John 7:53-8:11, Luke 22:43-44, 23:34)
    for bk, ch, vs in (('Mark', 16, range(8, 21)), ('John', 7, [53]), ('John', 8, range(1, 12)), ('Luke', 22, [43, 44]), ('Luke', 23, [34])):
        pg.goto(B + f'#/{bk}/{ch}'); pg.wait_for_selector('#v1')
        bad = [v for v in vs if pg.locator(f'#v{v} .w').count() == 0 or pg.locator(f'#v{v} .en3').count() != 1 or pg.locator(f'#v{v} .en.none').count()
               or re.search(r'[\[\]⟦⟧]', pg.inner_text(f'#v{v}'))]
        check(not bad, f'{bk} {ch}: Greek and English shown as normal text, no brackets or notes ({bad})')
    for (bk, ch, v), want in {('Mark', 16, 20): 'They went out and preached everywhere, the Lord working with them and confirming the word by the signs that followed.',
                               ('John', 8, 5): 'Now in our law, Moses commanded us to stone such women. What then do you say?”',
                               ('John', 8, 8): 'Again he stooped down and wrote on the ground.',
                               ('John', 8, 9): 'They, when they heard it, went out one by one, beginning from the oldest. He was left alone with the woman where she was, in the middle.',
                               ('John', 8, 10): 'Jesus, standing up, said to her, “Woman, where are they? Did no one condemn you?”',
                               ('John', 8, 11): 'She said, “No one, Lord.” Jesus said, “Neither do I condemn you. Go your way. From now on, sin no more.”'}.items():
        t = ven(bk, ch, v); check(t == want, f'HOLD closed: {bk} {ch}:{v} English is exactly Greek Maestro\'s ruling ({t[-50:]!r})')
    t = ven('Mark', 16, 8)
    check(t.startswith('They went out, and fled from the tomb') and t.endswith('for they were afraid. They briefly reported all that they had been commanded to Peter and those with him. After this, Jesus himself sent out through them, from the east to the west, the sacred and imperishable proclamation of eternal salvation. Amen.'),
          f'Mark 16:8: shorter-ending English (Greek Maestro, build/nt_english/overrides.tsv) follows the WEB ({t[-80:]!r})')
    A15, L20 = vjs('Acts', 15), vjs('Luke', 20)
    check(A15['17'][2].endswith('who does these things') and A15['18'][2] == 'known from eternity.’' and L20['30'][2] == 'The second' and L20['31'][2].startswith('and the third took her'), 'punctuation across joined verses: Acts 15:17-18 quote closes in v.18; Luke 20:30-31 one sentence')
    pg.close()
    check(not errs, f'no JS errors ({errs[:3]})')
print(f'\n{len(ok)} passed, {len(fails)} failed'); [print(' -', f) for f in fails]

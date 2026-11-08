#!/usr/bin/env python3
"""Headwords for 4 verbs, app-wide (LXX + NT), as reviewed by Greek Maestro (lemma_map_review.tsv):
ἀποκρίνω -> ἀποκρίνομαι, πορεύω -> πορεύομαι, φοβέω -> φοβέομαι: the entry is renamed in place (same id), so links/saved ids keep working.
ἀπολλύω -> ἀπόλλυμι: an ἀπόλλυμι entry already exists, so the ἀπολλύω entry is merged into it; data/lexredirect.json maps the old id.
Every word keeps its own form and grammar tag; the active forms stay in the same entry's forms table; the old headword and its
transliteration become search aliases (lexicon field 8). Idempotent. Run in site/, then nt_counts.py and pwa.py."""
import json, os, glob, unicodedata, collections
NTB = None
D = 'data'; N = lambda s: unicodedata.normalize('NFC', s)
L = json.load(open(f'{D}/lexicon.json')); NTB = {b['id'] for b in json.load(open(f'{D}/books.json')) if b.get('nt')}
def find(h): return [k for k, v in L.items() if N(v[0]) == N(h)]
BETA = {'ἀποκρίνομαι': 'a)pokri/nomai', 'πορεύομαι': 'poreu/omai', 'φοβέομαι': 'fobe/omai'}
RENAME = [('ἀποκρίνω', 'ἀποκρίνομαι', 'apokrinomai', 'separate, decide (rare active ἀποκρίνω)'),
          ('πορεύω', 'πορεύομαι', 'poreuomai', 'carry, convey (active πορεύω)'),
          ('φοβέω', 'φοβέομαι', 'phobeomai', 'frighten, terrify (active φοβέω)')]
st = collections.Counter()
for old, new, tr, act in RENAME:
    for k in find(old):
        v = L[k]
        while len(v) < 9: v.append([] if len(v) >= 7 else '')
        al = v[8]
        for a in (v[0], v[3]):
            if a and a not in al: al.append(a)
        v[0], v[3], v[4] = new, tr, BETA[new]
        if not any(x[0] == act for x in v[7]): v[7].append([act, 'W'])
        while len(v) < 9: v.append([])
        v[8] = al; st['renamed'] += 1
# merge ἀπολλύω into ἀπόλλυμι
RED = json.load(open(f'{D}/lexredirect.json')) if os.path.exists(f'{D}/lexredirect.json') else {}
src = [k for k in find('ἀπολλύω')]; dst = find('ἀπόλλυμι')
if src and dst:
    s, t = src[0], dst[0]; T = L[t]
    while len(T) < 9: T.append([])
    for a in ('ἀπολλύω', 'apolluō'):
        if a not in T[8]: T[8].append(a)
    T[3] = 'apollumi'; T[4] = 'a)po/llumi'; RED[s] = t
    si, ti = int(s), int(t)
    for f in glob.glob(f'{D}/*/*.json'):
        if f.split('/')[1] in ('dict', 'lsj', 'forms', 'occ', 'occnt', 'etym', 'en2', 'lx', 'bw', 'wk'): continue
        vs = json.load(open(f))
        if not isinstance(vs, list): continue
        ch = 0
        for v in vs:
            for w in v[1]:
                if w[1] == si: w[1] = ti; ch += 1
        if ch:
            json.dump(vs, open(f, 'w'), ensure_ascii=False, separators=(',', ':')); st['words_LXX' if not f.split('/')[1] in NTB else 'words_NT'] += ch
    for f in glob.glob(f'{D}/wk/*/*.json'):   # Wiktionary-layer links
        d = json.load(open(f)); ch = 0
        for vn in d.values():
            for i, x in vn.items():
                if str(x[0]) == s: x[0] = ti; ch += 1
        if ch: json.dump(d, open(f, 'w'), ensure_ascii=False, separators=(',', ':')); st['wk_links'] += ch
    fb = json.load(open(f'{D}/forms/{si // 100}.json')); tb = json.load(open(f'{D}/forms/{ti // 100}.json')) if si // 100 != ti // 100 else fb
    fs = fb.pop(s, None)
    if fs:
        e = tb.setdefault(t, {'f': [], 'b': {}}); e['f'] = e.get('f', []) + fs.get('f', [])
        for b, n in fs.get('b', {}).items(): e['b'][b] = e['b'].get(b, 0) + n
        json.dump(fb, open(f'{D}/forms/{si // 100}.json', 'w'), ensure_ascii=False, separators=(',', ':'))
        if tb is not fb: json.dump(tb, open(f'{D}/forms/{ti // 100}.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    ob = json.load(open(f'{D}/occ/{si // 100}.json')); tb = json.load(open(f'{D}/occ/{ti // 100}.json')) if si // 100 != ti // 100 else ob
    os_ = ob.pop(s, None)
    if os_:
        e = tb.get(t, [0]); refs = e[1:] + [r for r in os_[1:] if r not in e[1:]]
        order = {b['id']: i for i, b in enumerate(json.load(open(f'{D}/books.json')))}
        refs.sort(key=lambda r: (order.get(r.split('|')[0], 999), [int(x) if x.isdigit() else 0 for x in r.split('|')[1:]]))
        tb[t] = [e[0] + os_[0]] + refs
        json.dump(ob, open(f'{D}/occ/{si // 100}.json', 'w'), ensure_ascii=False, separators=(',', ':'))
        if tb is not ob: json.dump(tb, open(f'{D}/occ/{ti // 100}.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    c = json.load(open(f'{D}/counts.json'))
    if s in c: c[t] = c.get(t, 0) + c.pop(s); json.dump(c, open(f'{D}/counts.json', 'w'), separators=(',', ':'))
    nt = json.load(open(f'{D}/nt.json'))
    if s in nt and t not in nt: nt[t] = nt.pop(s); json.dump(nt, open(f'{D}/nt.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    del L[s]; st['merged'] += 1
json.dump(RED, open(f'{D}/lexredirect.json', 'w'))
json.dump(L, open(f'{D}/lexicon.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print(dict(st), 'redirects', RED)

#!/usr/bin/env python3
"""Daily Verses: build data/votd.json from build/votd/verses.tsv (ref<TAB>reason<TAB>source; 5 lines per calendar day, made by build/votd/pick.py).
Lines 5N-4 .. 5N (1-based) are shown on day N of a leap-year calendar (Jan 1 = 1, Feb 29 = 60, Mar 1 = 61 ... Dec 31 = 366), so a date
always gets the same five verses, in every year (1,830 verses, no repeats). Every ref must resolve to a verse in data/<book>/<ch>.json with Greek words and English
(LXX numbering, e.g. Ps 22:1 = Hebrew/English Ps 23:1). Latin comes from the content-checked Vulgate pairing (data/vp), if any (no Douay line).
Output: [[book, ch, verse, greek, english, latin], ...]"""
import json, os, re, sys
SITE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.join(SITE, 'data')
tsv = sys.argv[1] if len(sys.argv) > 1 else os.path.join(SITE, 'build', 'votd', 'verses.tsv')
rows = [l.rstrip('\n').split('\t') for l in open(tsv, encoding='utf-8') if l.strip()]
assert rows[0][:2] == ['ref', 'reason'], rows[0]
rows = rows[1:]
assert len(rows) == 366 * 5, len(rows)
books = {b['id']: b for b in json.load(open(os.path.join(D, 'books.json')))}
vulmap = json.load(open(os.path.join(D, 'vulmap.json'), encoding='utf-8'))
VUL_OVERRIDE = {
    'Mark 9:50': ('MRK', 9, '49'),
    '2Cor 1:24': ('2CO', 1, '23'),
    'Zech 2:14': ('ZEC', 2, '10'),
    'Zech 2:17': ('ZEC', 2, '13'),
    'Jer 38:31': ('JER', 31, '31'),
    'Jer 38:33': ('JER', 31, '33'),
    'Jer 39:27': ('JER', 32, '27'),
    'Sir 1:1h': ('SIR', 1, '1'),
    'Tob 4:7h': ('TOB', 4, '16'),
    'Jdt 7:28': ('JDT', 7, '19'),
    'Prov 24:61': ('PRO', 31, '9'),
}
def vul_text(vb, vc, vv):
    p = os.path.join(D, 'vul', vb, str(vc) + '.json')
    if not os.path.exists(p): return ''
    for y in json.load(open(p, encoding='utf-8')):
        if str(y[0]) == str(vv) and y[1]: return y[1]
    return ''
out, seen, bad = [], set(), []
for ref, why, *_ in rows:
    m = re.fullmatch(r'(\S+) (\d+):(\w+)', ref)
    if not m or m.group(1) not in books: bad.append(ref); continue
    b, c, v = m.groups()
    if ref in seen: bad.append('dup ' + ref); continue
    seen.add(ref)
    p = os.path.join(D, b, c + '.json')
    vs = {x[0]: x for x in json.load(open(p, encoding='utf-8'))} if os.path.exists(p) else {}
    x = vs.get(v)
    if not x or not x[1] or not x[2]: bad.append(ref); continue
    gk = ' '.join(t[0] for t in x[1])
    la = ''
    vpp = os.path.join(D, 'vp', b, c + '.json')
    if os.path.exists(vpp):
        pm = json.load(open(vpp, encoding='utf-8')).get(v)
        if pm: la = vul_text(pm[0], pm[1], pm[2])
    if not la and ref in VUL_OVERRIDE:
        la = vul_text(*VUL_OVERRIDE[ref])
    if not la:
        for entry in vulmap.get(f'{b}/{c}', []):
            la = vul_text(entry[0], entry[1], v)
            if la: break
    out.append([b, c, v, gk, x[2], la])
if bad: sys.exit('REFUSED: unresolved refs: ' + ', '.join(bad))
json.dump(out, open(os.path.join(D, 'votd.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(len(out), 'verses →', os.path.join(D, 'votd.json'), os.path.getsize(os.path.join(D, 'votd.json')), 'bytes;', sum(1 for o in out if o[5]), 'with Latin')

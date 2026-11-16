#!/usr/bin/env python3
"""Verse of the Day: build data/votd.json from build/votd/verses.tsv (ref<TAB>reason, one line per calendar day).
Line N (1-based) is shown on day N of a leap-year calendar (Jan 1 = 1, Feb 29 = 60, Mar 1 = 61 ... Dec 31 = 366), so a date
always gets the same verse, in every year. Every ref must resolve to a verse in data/<book>/<ch>.json with Greek words and English
(LXX numbering, e.g. Ps 22:1 = Hebrew/English Ps 23:1). Latin + Douay come from the content-checked Vulgate pairing (data/vp), if any.
Output: [[book, ch, verse, greek, english, latin, douay], ...]"""
import json, os, re, sys
SITE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.join(SITE, 'data')
tsv = sys.argv[1] if len(sys.argv) > 1 else os.path.join(SITE, 'build', 'votd', 'verses.tsv')
rows = [l.rstrip('\n').split('\t') for l in open(tsv, encoding='utf-8') if l.strip()]
assert rows[0] == ['ref', 'reason'], rows[0]
rows = rows[1:]
assert len(rows) == 366, len(rows)
books = {b['id']: b for b in json.load(open(os.path.join(D, 'books.json')))}
out, seen, bad = [], set(), []
for ref, why in rows:
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
    la = dr = ''
    vpp = os.path.join(D, 'vp', b, c + '.json')
    if os.path.exists(vpp):
        pm = json.load(open(vpp, encoding='utf-8')).get(v)
        vul = pm and os.path.join(D, 'vul', pm[0], str(pm[1]) + '.json')
        if vul and os.path.exists(vul):
            r = [y for y in json.load(open(vul, encoding='utf-8')) if y[0] == pm[2]]
            if r: la, dr = r[0][1] or '', r[0][2] or ''
    out.append([b, c, v, gk, x[2], la, dr])
if bad: sys.exit('REFUSED: unresolved refs: ' + ', '.join(bad))
json.dump(out, open(os.path.join(D, 'votd.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(len(out), 'verses →', os.path.join(D, 'votd.json'), os.path.getsize(os.path.join(D, 'votd.json')), 'bytes;', sum(1 for o in out if o[5]), 'with Latin')

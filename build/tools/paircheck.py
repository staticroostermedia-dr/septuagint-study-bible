#!/usr/bin/env python3
"""Verse-pairing check (Brenton Greek <-> Brenton English): for each verse, how many Greek content words have a dictionary gloss
(Dodson/TBESG/TFLSJ senses) found in the English verse with the same number, versus the previous/next English verse.
A verse is flagged when a neighbour fits clearly better. Output work/paircheck.tsv + summary."""
import json, os, re, collections, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from greek import vkey
D = '/workspace/lxx-cl/site/data'; W = '/workspace/lxx-cl/work'
LEX = json.load(open(D + '/lexicon.json')); MT = json.load(open(D + '/morph.json')); books = json.load(open(D + '/books.json'))
def stem(w): w = w.lower(); return w[:5]
GL = collections.defaultdict(set)
for k, L in LEX.items():
    for w in re.findall(r'[A-Za-z]{3,}', L[1] + ' ' + ' '.join(a[0] for a in (L[7] if len(L) > 7 else []))): GL[k].add(stem(w))
for f in os.listdir(D + '/dict'):
    for k, e in json.load(open(f'{D}/dict/{f}')).items():
        for s in e.get('s', [])[:6] + [e.get('g', '')]:
            for w in re.findall(r'[A-Za-z]{3,}', s): GL[k].add(stem(w))
names = lambda t: {w[:4].lower() for w in re.findall(r'\b[A-Z][a-z]+', t)}
rows = []; flag = 0; tot = 0; chap_flags = collections.Counter()
for b in books:
    for c in b['chapters']:
        vs = json.load(open(f"{D}/{b['id']}/{c}.json"))
        ens = [set(stem(w) for w in re.findall(r'[A-Za-z]{3,}', v[2] or '')) for v in vs]
        for i, v in enumerate(vs):
            ks = [str(t[1]) for t in v[1] if t[1] and str(t[1]) in GL and not MT[t[2]][0][:1] in ('R', 'C', 'P', 'X')]
            if len(ks) < 3 or not v[2]: continue
            tot += 1
            def sc(j): return sum(1 for k in ks if GL[k] & ens[j]) / len(ks) if 0 <= j < len(vs) else -1
            s0, sp, sn = sc(i), sc(i - 1), sc(i + 1)
            if max(sp, sn) > s0 + 0.25 and s0 < 0.35:
                flag += 1; chap_flags[f"{b['id']} {c}"] += 1
                rows.append(f"{b['id']} {c}:{v[0]}\t{s0:.2f}\t{sp:.2f}\t{sn:.2f}\t{' '.join(t[0] for t in v[1])[:120]}\t{(v[2] or '')[:120]}")
open(W + '/paircheck.tsv', 'w').write('ref\tscore_same\tscore_prev\tscore_next\tgreek\tenglish\n' + '\n'.join(rows) + '\n')
print('verses checked', tot, 'flagged (a neighbouring English verse fits clearly better)', flag)
print('chapters with >=3 flags', [(k, n) for k, n in chap_flags.most_common() if n >= 3])

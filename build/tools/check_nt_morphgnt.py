#!/usr/bin/env python3
"""Check only (MorphGNT is CC BY-SA and is NOT shipped or used to build data): compare NT lemma counts with MorphGNT-SBLGNT for its top-300 lemmas.
Usage: check_nt_morphgnt.py MORPHGNT_DIR  (run in site/). Prints exact-headword and accent-insensitive agreement (within ±2% or ±2)."""
import json, unicodedata, glob, collections, sys, re
N = lambda s: unicodedata.normalize('NFC', s)
def loose(s): return re.sub(r'[()]', '', ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn').lower())
mg = collections.Counter()
for f in glob.glob(sys.argv[1] + '/*-morphgnt.txt'):
    for l in open(f, encoding='utf-8'): mg[N(l.split()[-1])] += 1
L = json.load(open('data/lexicon.json')); n = json.load(open('data/ntcounts.json'))
ours = collections.Counter(); oursl = collections.Counter(); mgl = collections.Counter()
for k, c in n.items(): ours[N(L[k][0])] += c; oursl[loose(L[k][0])] += c
for k, c in mg.items(): mgl[loose(k)] += c
top = [w for w, _ in mg.most_common(300)]
ok = lambda a, b: abs(a - b) <= max(2, 0.02 * b)
ex = [(w, ours[w], mg[w]) for w in top]; lo = [(w, oursl[loose(w)], mgl[loose(w)]) for w in top]
print('top-300 MorphGNT lemmas within ±2%%/±2: exact headword %d/300; accent/iota/bracket-insensitive %d/300' % (sum(ok(a, b) for _, a, b in ex), sum(ok(a, b) for _, a, b in lo)))
print('remaining gaps (accent-insensitive):', [x for x in sorted(lo, key=lambda x: -abs(x[1] - x[2])) if not ok(x[1], x[2])][:30])

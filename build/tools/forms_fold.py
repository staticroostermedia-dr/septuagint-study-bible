#!/usr/bin/env python3
"""Fold forms-table rows (data/forms/*.json, LXX 'f' and NT 'nf') that differ only by capitalisation, a final grave
(instead of the dictionary acute), or an extra enclitic accent on the last syllable (λέγεί). Same grammar tag only.
Monosyllables keep their accents as written (εἰ/εἶ, ἤ/ἢ stay apart); breathing and non-final accents are never touched.
ALL-CAPS forms without diacritics (ΛΕΓΩΝ) are folded only into a single lowercase candidate with the same letters and tag.
Verse text is not changed. Idempotent. Run after nt_counts.py, before pwa.py. --report prints samples/skips."""
import json, glob, sys, unicodedata as U, collections
NFC = lambda s: U.normalize('NFC', s); NFD = lambda s: U.normalize('NFD', s)
AC, GR, CI = '\u0301', '\u0300', '\u0342'
VOW = set('αεηιουω')
def low(s):
    s = s.lower()
    return s[:-1] + 'ς' if s.endswith('σ') else s
def nuclei(d):   # syllable nuclei positions in an NFD string (diphthongs count once)
    base = [(i, c) for i, c in enumerate(d) if not U.combining(c)]; out = []; j = 0
    while j < len(base):
        i, c = base[j]
        if c in VOW:
            if j + 1 < len(base) and c + base[j + 1][1] in ('αι', 'ει', 'οι', 'υι', 'αυ', 'ευ', 'ηυ', 'ου') and not any(m == '\u0308' for m in d[base[j + 1][0] + 1:(base[j + 2][0] if j + 2 < len(base) else len(d))]):
                out.append((i, base[j + 1][0])); j += 2; continue
            out.append((i, i))
        j += 1
    return out
def key(f):
    s = NFD(low(NFC(f))); ns = nuclei(s)
    if len(ns) < 2: return NFC(s)
    acc = [k for k, c in enumerate(s) if c in (AC, GR, CI)]
    last0 = ns[-1][0]
    if len(acc) >= 2 and acc[-1] > last0 and s[acc[-1]] in (AC, GR): s = s[:acc[-1]] + s[acc[-1] + 1:]   # enclitic extra accent
    acc = [k for k, c in enumerate(s) if c in (AC, GR, CI)]
    if acc and s[acc[-1]] == GR and acc[-1] > last0: s = s[:acc[-1]] + AC + s[acc[-1] + 1:]          # final grave → acute
    return NFC(s)
bare = lambda f: ''.join(c for c in NFD(low(f)) if not U.combining(c))
def fold(rows, cap):
    groups = collections.OrderedDict()
    for r in rows: groups.setdefault((key(r[0]), r[1]), []).append(r)
    # all-caps rows with no diacritics → unique lowercase candidate with same letters and tag
    caps = [k for k, g in groups.items() if all(x[0].isupper() and NFD(x[0]) == x[0] for x in g)]
    skipped = []
    for k in caps:
        c = [k2 for k2 in groups if k2 != k and k2[1] == k[1] and k2 not in caps and bare(k2[0]) == bare(k[0])]
        n = sorted(((sum(x[2] for x in groups[k2]), k2) for k2 in c), reverse=True)
        if len(n) == 1 or (len(n) > 1 and n[0][0] >= 10 * n[1][0]): groups[n[0][1]] += groups.pop(k)   # one clear dictionary-accented match
        elif n: skipped.append((k[0], [(x[0], groups[x[1]][0][0]) for x in n], 'all-caps: no clear single match'))
    out, merges = [], []
    for (k, mi), g in groups.items():
        if len(g) == 1 and g[0][0] == k or len(g) == 1 and not any(x[0] != x[0].upper() for x in g) and False: out.append(g[0]); continue
        if len(g) == 1: out.append(g[0]); continue
        disp = k[0].upper() + k[1:] if cap and k[:1].islower() else k
        best = max(g, key=lambda x: x[2])
        out.append([disp, mi, sum(x[2] for x in g)] + best[3:]); merges.append((disp, [x[0] for x in g]))
    return out, merges, skipped
cap_lemma = lambda l: l[:1].isupper()
L = json.load(open('data/lexicon.json'))
tot = collections.Counter(); samples = []; skips = []
for fn in sorted(glob.glob('data/forms/*.json')):
    d = json.load(open(fn)); ch = False
    for lid, e in d.items():
        cap = cap_lemma(L.get(lid, [''])[0])
        for part, tag in (('f', 'LXX'), ('nf', 'NT')):
            if not e.get(part): continue
            new, m, sk = fold(e[part], cap)
            if m: e[part] = new; ch = True; tot[tag] += sum(len(x[1]) - 1 for x in m); tot[tag + '_groups'] += len(m); samples += [(tag, lid, x) for x in m]
            skips += [(tag, lid, x) for x in sk]
        # same form in LXX and NT tables: use one spelling so the app's merged table shows one row
        if e.get('f') and e.get('nf'):
            cap = cap_lemma(L.get(lid, [''])[0]); disp = lambda k: k[0].upper() + k[1:] if cap and k[:1].islower() else k
            fk = {(key(r[0]), r[1]): r for r in e['f']}
            for r in e['nf']:
                k = (key(r[0]), r[1]); o = fk.get(k)
                if o and o[0] != r[0]:
                    o[0] = r[0] = disp(k[0]); ch = True; tot['LXX_NT_aligned'] += 1; samples.append(('LXX+NT', lid, (r[0], 'aligned')))
    if ch: json.dump(d, open(fn, 'w'), ensure_ascii=False, separators=(',', ':'))
print(dict(tot))
if '--report' in sys.argv:
    import random; random.seed(7)
    for s in random.sample(samples, min(15, len(samples))): print('merge', s)
    for s in skips[:20]: print('skip', s)

#!/usr/bin/env python3
"""'Also in the NT': up to 3 NT references per LXX lemma.
Source: STEPBible TAGNT (Translators Amalgamated Greek NT, STEPBible.org, CC BY 4.0), words in NA28.
Inputs /workspace/src/tagnt/{mj,ar}.txt. Matching: lemma normalised (NFC, accents/breathings stripped, final sigma, lower case).
Output data/nt.json {lid: [count, "Matt 5:3", ...]} (lemmas not in the NT are omitted)."""
import json, os, re, unicodedata as u, collections
HERE = os.path.dirname(os.path.abspath(__file__)); D = '/workspace/lxx-cl/site/data'
def norm(s):
    s = ''.join(c for c in u.normalize('NFD', s) if not u.combining(c)).lower().replace('ς', 'σ')
    return u.normalize('NFC', re.sub(r'[^\w]', '', s))
BK = dict(zip('Mat Mrk Luk Jhn Act Rom 1Co 2Co Gal Eph Php Col 1Th 2Th 1Ti 2Ti Tit Phm Heb Jas 1Pe 2Pe 1Jn 2Jn 3Jn Jud Rev'.split(),
    ['Matt', 'Mark', 'Luke', 'John', 'Acts', 'Rom', '1 Cor', '2 Cor', 'Gal', 'Eph', 'Phil', 'Col', '1 Thess', '2 Thess', '1 Tim', '2 Tim',
     'Titus', 'Phlm', 'Heb', 'Jas', '1 Pet', '2 Pet', '1 John', '2 John', '3 John', 'Jude', 'Rev']))
refs, cnt = collections.defaultdict(list), collections.Counter()
for f in ('mj.txt', 'ar.txt'):
    for l in open(f'/workspace/src/tagnt/{f}', encoding='utf-8'):
        m = re.match(r'([0-9A-Z][0-9A-Za-z]{2})\.(\d+)\.(\d+)#', l)
        if not m or m.group(1) not in BK: continue
        c = l.rstrip('\n').split('\t')
        if len(c) < 6 or 'NA28' not in c[5]: continue
        lem = norm(c[4].split('=')[0])
        if not lem: continue
        cnt[lem] += 1; r = f'{BK[m.group(1)]} {m.group(2)}:{m.group(3)}'
        if len(refs[lem]) < 3 and r not in refs[lem]: refs[lem].append(r)
L = json.load(open(f'{D}/lexicon.json')); out = {}
for k, e in L.items():
    n = norm(e[0])
    if n in cnt: out[k] = [cnt[n]] + refs[n]
json.dump(out, open(f'{D}/nt.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print('ntrefs: NT lemmas', len(cnt), '; LXX lemmas also in NT', len(out), 'of', len(L), '; bytes', os.path.getsize(f'{D}/nt.json'))

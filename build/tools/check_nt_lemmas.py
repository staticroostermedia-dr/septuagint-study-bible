#!/usr/bin/env python3
"""Does the word card's headword agree with TAGNT's dictionary form for every NT word? Usage: check_nt_lemmas.py TAGNT_DIR (run in site/)"""
import json, os, re, sys, unicodedata, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import tagnt_na28
def n(s): return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn').lower().replace('ς', 'σ')
lex = json.load(open('data/lexicon.json')); tag = []
PUN = re.compile('[\u037e\\[\\]().,;:\u00b7\u0387\u2e00-\u2e05\u2014\u2013\u201c\u201d"\u00ab\u00bb\u00b6]')
for fn in ('mj.txt', 'ar.txt'):
    for l in open(sys.argv[1] + '/' + fn, encoding='utf-8'):
        f = l.rstrip('\n').split('\t')
        m = tagnt_na28.REF.match(f[0]); r = tagnt_na28.row(m, f, sys.argv[1]) if m and len(f) > 5 else None
        if r and PUN.sub('', r[0]).strip(): tag.append(r[3])
ours = []
for b in [b for b in json.load(open('data/books.json')) if b.get('nt')]:
    for c in b['chapters']:
        for v in json.load(open(f"data/{b['id']}/{c}.json")): ours += [w[1] for w in v[1]]
assert len(tag) == len(ours), (len(tag), len(ours))
mm = collections.Counter(); same = 0
for t, i in zip(tag, ours):
    h = lex[str(i)][0]
    if n(h) == n(t.split(',')[0]): same += 1
    else: mm[(t, h)] += 1
print('NT card headword agrees with TAGNT dictionary form: %d/%d = %.2f%%' % (same, len(ours), 100 * same / len(ours)))
print('differences (TAGNT form, card headword, count):', mm.most_common(10))

#!/usr/bin/env python3
"""Wiktionary (kaikki.org Wiktextract, CC BY-SA 4.0) form -> lemma for forms no CC BY / MPL route covered. Separate layer."""
import json, sys, os, collections, unicodedata as u
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from greek import *
W = '/workspace/lxx-cl/work'
A = json.load(open(W + '/analysis_raw.json'))
need = {f for f in open(W + '/forms.txt').read().split('\n') if f and f not in A}
def key(s): return lower_form(u.normalize('NFC', u.normalize('NFD', s).replace('\u0306', '').replace('\u0304', '')))
hits = collections.defaultdict(collections.Counter); tags = {}
for l in open('/workspace/src/grc_kaikki.jsonl', encoding='utf-8'):
    d = json.loads(l); w = d.get('word', ''); pos = d.get('pos', '')
    kw = key(w)
    if kw in need:
        for s in d.get('senses', []):
            for fo in s.get('form_of', []) or []:
                hits[kw][(fo['word'], pos)] += 2; tags[(kw, fo['word'])] = s.get('tags', [])
        if not any(s.get('form_of') for s in d.get('senses', [])) and pos in ('name', 'noun', 'adj', 'verb', 'adv', 'num', 'prep', 'conj', 'particle', 'pron', 'intj'):
            hits[kw][(w, pos)] += 3; tags.setdefault((kw, w), ['lemma'])
    for fm in d.get('forms', []) or []:
        if fm.get('source') != 'inflection' and 'declension' not in fm.get('source', '') and 'conjugation' not in fm.get('source', ''): continue
        kf = key(fm.get('form', ''))
        if kf in need and 'romanization' not in fm.get('tags', []):
            hits[kf][(w, pos)] += 1; tags.setdefault((kf, w), fm.get('tags', []))
out = {}
for f, c in hits.items():
    (lem, pos), n = c.most_common(1)[0]
    out[f] = {'src': 'K', 'wk': [key(lem) if False else u.normalize('NFC', u.normalize('NFD', lem).replace('\u0306', '').replace('\u0304', '')), pos, tags.get((f, lem), [])], 'alt': len(c)}
json.dump(out, open(W + '/analysis_wikt.json', 'w'), ensure_ascii=False)
print('wiktionary layer: forms needing a lemma', len(need), 'found', len(out))

#!/usr/bin/env python3
"""Descendants layer (Wiktionary 'Descendants' sections via kaikki.org / Wiktextract dumps, CC BY-SA 4.0), kept separate like data/etym/.
Greek: data/desc/<lid//100>.json  {lid: [[lang, word], ...]}   Latin: data/ldesc/<li//500>.json  {li: [[lang, word], ...]}
Only the exact dictionary form is used (same headword after removing vowel-length marks; Latin also exact case). Never a related form.
If Wiktionary has several entries for that headword with different descendant lists, the one whose part of speech matches is used;
if that still leaves more than one different list, nothing is shown (counted as ambiguous). Same with lexicon homographs.
Lists are flattened (nested descendants follow their parent), wordless grouping nodes are skipped, duplicates dropped, capped at 80.
Input dumps: /workspace/src/grc_kaikki.jsonl, /workspace/src/lat_kaikki.jsonl (downloaded 2026-11-06, local; nothing is fetched here)."""
import collections, json, os, sys, unicodedata
SITE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.join(SITE, 'data'); CAP = 80
def nw(s): return unicodedata.normalize('NFC', ''.join(c for c in unicodedata.normalize('NFD', s) if c not in '\u0304\u0306'))
def flat(ds, depth=0, out=None, seen=None):
    out = [] if out is None else out; seen = set() if seen is None else seen
    for d in ds or []:
        w, lang = (d.get('word') or '').strip(), (d.get('lang') or '').strip()
        if w and lang and d.get('lang_code') != 'unknown' and (lang, w) not in seen and not w.startswith('(') :
            seen.add((lang, w)); out.append([lang, w])
        if depth < 4: flat(d.get('descendants'), depth + 1, out, seen)
    return out
import re
STOP = set('a an the of to in on or and for with by as be is at from one who which that his her its it not up out off'.split())
def toks(t): return {w for w in re.findall(r'[a-z]+', (t or '').lower()) if len(w) > 2 and w not in STOP}
def pick(cands, okpos, gloss=''):
    """cands: [(pos, list, sense glosses)] for the exact headword. Returns the list, or None (absent) / 'AMB' (ambiguous).
    Several different lists: keep those whose part of speech matches; if still several (homographs such as caelum 'sky' / caelum 'chisel'),
    keep the one whose Wiktionary senses share the most words with our own meaning, if exactly one does."""
    cands = [c for c in cands if c[1]]
    if not cands: return None
    if len({json.dumps(c[1]) for c in cands}) == 1: return cands[0][1]
    m = [c for c in cands if c[0] in okpos] or cands
    if len({json.dumps(c[1]) for c in m}) == 1: return m[0][1]
    g = toks(gloss); sc = sorted(((len(g & toks(c[2])), i) for i, c in enumerate(m)), reverse=True)
    if sc[0][0] > 0 and (len(sc) == 1 or sc[1][0] < sc[0][0]): return m[sc[0][1]][1]
    return 'AMB'
def scan(path, lang_code, keyf):
    idx = collections.defaultdict(list)
    with open(path, encoding='utf-8') as f:
        for line in f:
            if '"descendants"' not in line: continue
            e = json.loads(line)
            if e.get('lang_code') != lang_code or not e.get('descendants'): continue
            gl = ' '.join(g for sn in e.get('senses', []) for g in sn.get('glosses', []))
            idx[keyf(e.get('word', ''))].append((e.get('pos', ''), flat(e['descendants'])[:CAP], gl))
    return idx
GPOS = {'Noun': {'noun'}, 'Noun (name)': {'name', 'noun'}, 'Verb': {'verb'}, 'Adjective': {'adj', 'num'}, 'Adverb': {'adv'}, 'Adverb (name)': {'adv', 'name'},
        'Preposition': {'prep'}, 'Conjunction': {'conj'}, 'Particle': {'particle'}, 'Pronoun': {'pron', 'det'}, 'Personal': {'pron'}, 'Demonstrative': {'pron', 'det'},
        'Interrogative/indefinite': {'pron', 'det'}, 'Interjection': {'intj'}, 'Article': {'article', 'det'}, 'Numeral': {'num', 'adj'}}
LPOS = {'NOUN': {'noun'}, 'PROPN': {'name', 'noun'}, 'VERB': {'verb'}, 'AUX': {'verb'}, 'ADJ': {'adj', 'num', 'participle'}, 'ADV': {'adv'}, 'ADP': {'prep', 'postp'},
        'CCONJ': {'conj'}, 'SCONJ': {'conj'}, 'PART': {'particle', 'adv'}, 'DET': {'det', 'pron', 'adj'}, 'PRON': {'pron'}, 'NUM': {'num', 'adj'}, 'INTJ': {'intj'}}
stats = {}
# Greek
lex = json.load(open(os.path.join(D, 'lexicon.json'), encoding='utf-8'))
G = scan('/workspace/src/grc_kaikki.jsonl', 'grc', nw)
homo = collections.Counter(nw(L[0]) for L in lex.values())
out = collections.defaultdict(dict); n = amb = 0
for k, L in lex.items():
    h = nw(L[0]); cands = G.get(h, [])
    if homo[h] > 1: cands = [c for c in cands if c[0] in GPOS.get(L[2], set())]   # lexicon homographs: part of speech must match
    r = pick(cands, GPOS.get(L[2], set()), L[1])
    if r == 'AMB': amb += 1; continue
    if r: out[int(k) // 100][k] = r; n += 1
for d in ('desc',):
    os.makedirs(os.path.join(D, d), exist_ok=True)
    for f in os.listdir(os.path.join(D, d)): os.remove(os.path.join(D, d, f))
for bk, d in out.items(): json.dump(d, open(os.path.join(D, 'desc', f'{bk}.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
stats['greek'] = {'entries': len(lex), 'with_descendants': n, 'ambiguous_skipped': amb, 'items': sum(len(v) for d in out.values() for v in d.values())}
# Latin
latlex = json.load(open(os.path.join(D, 'latlex.json'), encoding='utf-8'))
def uv(w): return nw(w).replace('v', 'u').replace('V', 'U').replace('j', 'i').replace('J', 'I')   # our Latin lemmas spell u/i (uideo); Wiktionary v/j (video)
LT = scan('/workspace/src/lat_kaikki.jsonl', 'la', nw)
LTu = collections.defaultdict(list)
for w, cs in LT.items(): LTu[uv(w)].extend(cs)
LSH = {}
for f in os.listdir(os.path.join(D, 'ls')): LSH.update(json.load(open(os.path.join(D, 'ls', f), encoding='utf-8')))
lhomo = collections.Counter(X[0] for X in latlex)
lout = collections.defaultdict(dict); ln = lamb = 0
for li, X in enumerate(latlex):
    cands = LT.get(nw(X[0])) or LTu.get(uv(X[0]), [])   # same form; only the u/v, i/j spelling may differ
    if lhomo[X[0]] > 1: cands = [c for c in cands if c[0] in LPOS.get(X[1], set())]
    ls = LSH.get(str(X[2])) if len(X) > 2 else None
    r = pick(cands, LPOS.get(X[1], set()), ls[1] if ls else '')
    if r == 'AMB': lamb += 1; continue
    if r: lout[li // 500][str(li)] = r; ln += 1
os.makedirs(os.path.join(D, 'ldesc'), exist_ok=True)
for f in os.listdir(os.path.join(D, 'ldesc')): os.remove(os.path.join(D, 'ldesc', f))
for bk, d in lout.items(): json.dump(d, open(os.path.join(D, 'ldesc', f'{bk}.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
stats['latin'] = {'entries': len(latlex), 'with_descendants': ln, 'ambiguous_skipped': lamb, 'items': sum(len(v) for d in lout.values() for v in d.values())}
size = sum(os.path.getsize(os.path.join(D, d, f)) for d in ('desc', 'ldesc') for f in os.listdir(os.path.join(D, d)))
stats['bytes'] = size
print(json.dumps(stats))
json.dump(stats, open(os.path.join(SITE, 'build', 'desc_stats.json'), 'w'), indent=1)

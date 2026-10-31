#!/usr/bin/env python3
"""CLEAN build: plain-English headline meaning. Dodson (PD / CC0) first, then STEPBible TBESG brief gloss (CC BY 4.0),
then the hand-written layer (tools/gloss_hand_plain.tsv, label 'hand-written'). No LXX lexicon (CCAT 09a) is read.
Text changes (as in preview-changes): spacing tidied; leading I/to/a/an/the removed; Dodson 'am X' -> 'be X'; TBESG 'base: specific' -> base;
Dodson glosses with >3 senses or >40 characters shortened to at most 3 of their own senses (full gloss under More)."""
import json, os, re, unicodedata as u, collections
HERE = os.path.dirname(os.path.abspath(__file__)); D = '/workspace/lxx-cl/site/data'
LP = f'{D}/lexicon.json'
L = json.load(open(LP)); L = {k: e[:6] for k, e in L.items()}; CNT = json.load(open(f'{D}/counts.json'))
def norm(s):
    s = ''.join(c for c in u.normalize('NFD', s) if not u.combining(c)).lower().replace('ς', 'σ')
    return u.normalize('NFC', re.sub(r'[^\w]', '', s))
def tidy(g, verb):
    g = re.sub(r'\s+', ' ', g or '').strip(' .;,')
    g = g.split(': ')[0]                                   # TBESG 'lord: God' = base gloss: specific sense -> base gloss
    parts = []
    for p in g.split(', '):
        p = re.sub(r'^I (?=[a-z])', '', p)
        p = re.sub(r'^to ', '', p) if verb else re.sub(r'^(a|an|the) ', '', p)
        p = re.sub(r'^am\b', 'be', p)                         # Dodson's 1st-person 'am able' -> 'be able'
        if p and p not in parts: parts.append(p)
    return ', '.join(parts)
def shorten(g, others):
    parts = g.split(', ')
    if len(parts) <= 3 and len(g) <= 40: return g
    ow = {w[:5] for w in re.findall(r'[a-z]{3,}', ' '.join(others).lower())}
    keep = [parts[0]] + [p for p in parts[1:] if {w[:5] for w in re.findall(r'[a-z]{3,}', p.lower())} & ow]
    for p in parts[1:]:
        if len(keep) >= 2: break
        if p not in keep: keep.append(p)
    keep = [p for p in parts if p in keep][:3]
    return ', '.join(keep)
# --- Dodson
DOD_S, DOD_L = {}, collections.defaultdict(list)
x = open('/workspace/src/dodson/dodson.xml', encoding='utf-8').read()
for m in re.finditer(r'<entry n="([^"|]+)\| (\d+)">.*?<def role="brief">(.*?)</def>', x, re.S):
    lem, st, g = m.group(1).strip(), 'G' + str(int(m.group(2))), re.sub(r'\s+', ' ', m.group(3)).strip()
    DOD_S[st] = (lem, g); DOD_L[norm(lem)].append((st, g))
def dict_g(k):
    try: return (json.load(open(f'{D}/dict/{int(k)//100}.json')).get(k) or {}).get('g', '')
    except Exception: return ''
POS_CONTENT = ('Noun', 'Verbs', 'Adjective', 'Adverb')
stat = collections.Counter(); review = []
for k, e in L.items():
    verb = e[2].startswith('Verb'); B = ''; bsrc = ''
    st = e[5] if re.match(r'^G\d+$', e[5] or '') else ''
    dg = ''
    if st and st in DOD_S and norm(DOD_S[st][0]) == norm(e[0]): dg = DOD_S[st][1]; stat['dodson strong+lemma'] += 1
    elif len(DOD_L.get(norm(e[0]), [])) == 1: dg = DOD_L[norm(e[0])][0][1]; stat['dodson lemma only'] += 1
    dg = tidy(dg, verb); tg = tidy(dict_g(k), verb)
    if dg: head, src = shorten(dg, [tg, B]), 'D'
    elif tg: head, src = tg, 'T'
    else: head, src = B, bsrc
    alts, seen = [], {norm(head)}
    cand = [(B, bsrc)]
    cand += [(dg, 'D'), (tg, 'T')]   # full Dodson gloss kept if the headline was shortened
    for t, s in cand:
        if t and norm(t) not in seen: seen.add(norm(t)); alts.append([t, s])
    L[k] = e[:6] + [src, alts] if alts else e[:6] + [src]
    L[k][1] = head; stat['src ' + src] += 1
    review.append((k, e[0], CNT.get(k, 0), e[2], dg, tg, B, bsrc, head, src))
# --- hand-written override layer (tools/gloss_hand_plain.tsv; label W = 'hand-written'); the original wording stays under More
HW = {}
for l in open(os.path.join(HERE, 'gloss_hand_plain.tsv'), encoding='utf-8'):
    if '\t' in l and not l.startswith('#'):
        c = l.rstrip('\n').split('\t'); HW[norm(c[0])] = c
SRCN = {'Dodson': 'D', 'STEP Bible': 'T'}
hw_done = set()
for k, e in L.items():
    c = HW.get(norm(e[0]))
    if not c or '(name)' in e[2]: continue
    lab, orig = c[2].split(': ', 1)
    old = ([[e[1], e[6]]] if e[1] else []) + (e[7] if len(e) > 7 else [])
    alts, seen = [], {norm(c[1])}
    for t, sc in [[orig, SRCN.get(lab, e[6])]] + old:
        if norm(t) not in seen: seen.add(norm(t)); alts.append([t, sc])
    L[k] = e[:6] + ['W', alts]; L[k][1] = c[1]; hw_done.add(norm(e[0]))
    for i, r in enumerate(review):
        if r[0] == k: review[i] = r[:8] + (c[1], 'W')
assert hw_done == set(HW), ('hand-written lemmas not found', set(HW) - hw_done)
stat['hand-written'] = len(hw_done)
json.dump(L, open(LP, 'w'), ensure_ascii=False, separators=(',', ':'))

cov = sum(1 for e in L.values() if e[1]); print('plainmeaning:', dict(stat), 'lemmas with a meaning', cov, 'of', len(L))

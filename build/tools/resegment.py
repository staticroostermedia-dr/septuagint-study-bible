#!/usr/bin/env python3
"""Verse-boundary repair (general rule, no per-verse hand edits).
Brenton's English sometimes divides verses at a different place from his own Greek as printed by eBible (a clause sits one verse early
or late). For each pair of neighbouring verses, the English is cut at punctuation (, ; : . ? !). A clause at the boundary moves to the neighbouring verse when the
word-translation model trained on all Brenton verse pairs explains it much better by the neighbouring Greek verse (average gain >= RS_T
nats per content word, at least 2 content words). A verse is emptied only if the next verse can refill it. Changed verses get v[3] = {'s': 'r'}.
The original English is kept in work/orig_en/ so the step is repeatable. Report: work/reseg_report.tsv."""
import json, os, re, collections, sys, math
D = '/workspace/lxx-cl/site/data'; W = '/workspace/lxx-cl/work'; MIN_GAIN = int(os.environ.get('RS_GAIN', '2'))
LEX = json.load(open(D + '/lexicon.json')); MT = json.load(open(D + '/morph.json')); books = json.load(open(D + '/books.json'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import unicodedata as _u
def _n(s): return _u.normalize('NFC', ''.join(c for c in _u.normalize('NFD', s) if not _u.combining(c)).lower().replace('ς', 'σ'))
from brentalign_lite import stem, EFUNC, TOK, load_model
TGE, TEG = ({}, {}) if os.environ.get('RS_RESTORE') else load_model(W + '/brentalign_model_pairs_v1.json', both=True)   # frozen copy: the model trained on the original (unadjusted) verse pairs   # p(e|g) from the IBM Model 1 trained on the Brenton pairs (work/brentalign_model.json)
T = float(os.environ.get('RS_T', '1.5'))
def gks(v): return ['<N>'] + [str(t[1]) if t[1] else 'f:' + _n(t[0]) for t in v[1] if not MT[t[2]][0].startswith('RA')]
def ews(cl): return [stem(w) for w in TOK.findall(cl) if w.lower() not in EFUNC]
def cfg(Es, Gs):
    """log-likelihood of English given Greek and of Greek content words given English, both ways (IBM Model 1, with a null word)."""
    tot = 0.0
    for E, G in zip(Es, Gs):
        es = ews(join(E)); gc = [g for g in G[1:] if not g.startswith('f:')]
        tot += sum(math.log(sum(TGE.get((g, e), 1e-7) for g in G) / len(G)) for e in es)
        tot += sum(math.log(sum(TEG.get((e, g), 1e-7) for e in ['<N>'] + es) / (len(es) + 1)) for g in gc)
    return tot
def gain(Eold, Enew, Gs, moved):
    n = len(ews(join(moved))); g = cfg(Enew, Gs) - cfg(Eold, Gs)
    return g if n >= 2 and g / n >= T else 0
def clauses(t): return [c for c in re.split(r'(?<=[,;:.?!])\s+', (t or '').strip()) if c]
def join(cs): return ' '.join(cs)
rep = []; nch = 0
for b in books:
    for c in b['chapters']:
        p = f"{D}/{b['id']}/{c}.json"; o = f"{W}/orig_en/{b['id']}_{c}.json"
        vs = json.load(open(p))
        if os.path.exists(o): en = json.load(open(o))
        else: en = [v[2] for v in vs]; json.dump(en, open(o, 'w'), ensure_ascii=False)
        for v, e in zip(vs, en):
            v[2] = e
            if len(v) > 3 and isinstance(v[3], dict) and v[3].get('s') == 'r': v.pop(3)
        if os.environ.get('RS_RESTORE'):
            json.dump(vs, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':')); continue
        E = [clauses(e) for e in en]; G = [gks(v) for v in vs]; changed = set()
        for i in [j for _ in range(int(os.environ.get('RS_PASSES', '2'))) for j in range(len(vs) - 1)]:
            old = [E[i], E[i + 1]]; best = (0, None)
            for k in range(1, len(E[i])):                       # last k clauses of verse i -> verse i+1
                g = gain(old, [E[i][:-k], E[i][-k:] + E[i + 1]], G[i:i + 2], E[i][-k:])
                if g > best[0]: best = (g, ('back', k))
            for k in range(1, len(E[i + 1]) + 1):               # first k clauses of verse i+1 -> verse i
                if k == len(E[i + 1]) and not (i + 2 < len(vs) and E[i + 2]): break
                g = gain(old, [E[i] + E[i + 1][:k], E[i + 1][k:]], G[i:i + 2], E[i + 1][:k])
                if g > best[0]: best = (g, ('fwd', k))
            if best[1]:
                d, k = best[1]
                if d == 'back': E[i], E[i + 1] = E[i][:-k], E[i][-k:] + E[i + 1]
                else: E[i], E[i + 1] = E[i] + E[i + 1][:k], E[i + 1][k:]
                rep.append(f"{b['id']} {c}:{vs[i][0]}-{vs[i + 1][0]}\t{d}\t{k}\tgain {best[0]:.1f}"); changed |= {i, i + 1}
        for i in changed:
            vs[i][2] = join(E[i]) or None
            while len(vs[i]) < 3: vs[i].append(None)
            if len(vs[i]) == 3: vs[i].append({'s': 'r'})
            elif isinstance(vs[i][3], dict): vs[i][3]['s'] = vs[i][3].get('s') or 'r'
            else: vs[i][3] = {'s': 'r'}
        if changed: nch += 1
        json.dump(vs, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
open(W + '/reseg_report.tsv', 'w').write('\n'.join(rep) + '\n')
print('restored original English' if os.environ.get('RS_RESTORE') else 'boundary moves', len(rep), 'chapters changed', nch)

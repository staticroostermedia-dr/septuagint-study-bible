#!/usr/bin/env python3
"""'Brenton's wording': likely English word in the displayed Brenton verse for each Greek token.
Brenton is not word-aligned, so this is an automatic statistical alignment built here:
  IBM Model 1 trained in both directions (Greek lemma <-> English stem) on all displayed verse pairs,
  x a diagonal position prior, x a bonus when the English word matches the lemma's dictionary glosses
  (site lexicon + STEPBible TBESG senses), then one-to-one competitive linking per verse.
Greek articles never get a link; English function words can only link to Greek function words.
Each link gets a confidence = its share of the token's alignment mass; links under THRESH are dropped (abstain).
Output: site/data/bw/<Book>/<ch>.json  {verse: [0 | [charStart, charEnd, conf%], ... per Greek token]}
Usage: brentalign.py [--sample N]  (writes tools/brentalign_sample.tsv for hand checking)"""
import json, os, re, sys, math, collections, random
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, '..', 'site', 'data')
THRESH = float(os.environ.get('BW_THRESH', 0.5))
books = json.load(open(D + '/books.json')); LEX = json.load(open(D + '/lexicon.json')); MT = json.load(open(D + '/morph.json'))
ARCH = {'thee': 'you', 'thou': 'you', 'ye': 'you', 'thy': 'your', 'thine': 'your', 'hath': 'have', 'hast': 'have', 'had': 'have', 'has': 'have',
        'saith': 'say', 'said': 'say', 'doth': 'do', 'did': 'do', 'art': 'be', 'is': 'be', 'are': 'be', 'was': 'be', 'were': 'be', 'been': 'be', 'shalt': 'shall',
        'wilt': 'will', 'came': 'come', 'went': 'go', 'gave': 'give', 'given': 'give', 'took': 'take', 'taken': 'take', 'spoke': 'speak', 'spake': 'speak', 'spoken': 'speak',
        'saw': 'see', 'seen': 'see', 'made': 'make', 'brought': 'bring', 'men': 'man', 'children': 'child', 'sons': 'son', 'heard': 'hear', 'knew': 'know', 'known': 'know',
        'sat': 'sit', 'stood': 'stand', 'ate': 'eat', 'eaten': 'eat', 'begat': 'beget', 'begot': 'beget', 'smote': 'smite', 'slew': 'slay', 'slain': 'slay', 'fled': 'flee',
        'wrote': 'write', 'written': 'write', 'told': 'tell', 'sent': 'send', 'set': 'set', 'put': 'put', 'built': 'build', 'fell': 'fall', 'fallen': 'fall', 'rose': 'rise',
        'risen': 'rise', 'arose': 'arise', 'drank': 'drink', 'found': 'find', 'brethren': 'brother', 'feet': 'foot', 'women': 'woman', 'oxen': 'ox', 'kept': 'keep', 'left': 'leave', 'led': 'lead', 'dwelt': 'dwell'}
EFUNC = set('shalt wilt mayest canst wouldest couldest let ye thou thee thy thine hath hast art doth dost thereof therein whereof thereby whosoever whatsoever the a an of to and in on at by for from with into unto upon as that this these those it its he him his she her they them their we us our you your i me my mine be shall will would should may might can could do not no nor or but if then so all which who whom whose what when where there here also even yet up out over under before after against about through every any'.split())
def stem(w):
    w = w.lower(); w = ARCH.get(w, w)
    for suf in ('eth', 'est', 'ing', 'edst', 'ed', 'es', 's'):
        if len(w) > len(suf) + 3 and w.endswith(suf): w = w[:-len(suf)]; break
    return w[:6]
TOK = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")
def gfunc(code): p = code.split('.')[0]; return p.startswith('R') or p in ('C', 'P', 'X', 'D', 'I') or '+' in p
# gloss vocabulary per lemma (dictionary prior)
GL = collections.defaultdict(set)
def addg(lid, text):
    for w in TOK.findall(text or ''):
        if w.lower() not in EFUNC: GL[lid].add(stem(w))
for lid, L in LEX.items(): addg(lid, L[1])
for f in os.listdir(D + '/dict'):
    for lid, e in json.load(open(f'{D}/dict/{f}')).items(): addg(lid, e.get('g', '')); [addg(lid, s) for s in e.get('s', [])[:6]]
for f in os.listdir(D + '/lsj'):     # LSJ (STEPBible TFLSJ) senses too: covers LXX-only words Abbott-Smith lacks
    for lid, e in json.load(open(f'{D}/lsj/{f}')).items(): [addg(lid, s) for s in e.get('s', [])[:6]]
# corpus
pairs = []
for bk in books:
    if not bk.get('en'): continue
    for c in bk['chapters']:
        for v in json.load(open(f"{D}/{bk['id']}/{c}.json")):
            if not v[2]: continue
            st = v[3] if len(v) > 3 else None
            ets = [(m.start(), m.end(), m.group()) for m in TOK.finditer(v[2])]
            pairs.append((bk['id'], c, v[0], v[1], ets, v[2], st))
print(len(pairs), 'verse pairs', file=sys.stderr)
GFREQ = collections.Counter(str(t[1]) for p in pairs for t in p[3])
RARE = int(os.environ.get('BW_RARE', 3)); RARE_CONF = float(os.environ.get('BW_RARE_CONF', 0.9))
# Rare lemmas (seen only once or twice in verses with English): the statistics are too thin to trust on their own,
# so a link that is not backed by the lemma's dictionary glosses (and is not name-to-name) needs confidence >= RARE_CONF.
# (Added 2026-10-31 after the hand check found 'crew' for αὐθέντας and "woman's" for ἐπεκοιμήθη — both rare lemmas, no gloss support.)
GS = lambda p: [str(t[1]) for t in p[3] if not MT[t[2]][0].startswith('RA')]
ES = lambda p: [stem(e[2]) for e in p[4]]
def ibm1(src, tgt, iters=5):
    t = None
    for it in range(iters):
        cnt = collections.Counter(); tot = collections.Counter()
        for p in pairs:
            S = ['<N>'] + src(p)
            for x in tgt(p):
                ws = [1.0] * len(S) if t is None else [t.get((s, x), 1e-7) for s in S]; z = sum(ws)
                for s, w in zip(S, ws): cnt[(s, x)] += w / z; tot[s] += w / z
        t = {k: v / tot[k[0]] for k, v in cnt.items() if v / tot[k[0]] > 1e-4}
        print('ibm1 iter', it, len(t), file=sys.stderr)
    return t
CACHE = os.path.join(HERE, '.brentalign_model.json')
if os.path.exists(CACHE) and '--retrain' not in sys.argv:
    m = json.load(open(CACHE)); TGE = {tuple(k.split('\t')): v for k, v in m['ge'].items()}; TEG = {tuple(k.split('\t')): v for k, v in m['eg'].items()}
else:
    TGE = ibm1(GS, ES); TEG = ibm1(ES, GS)   # TGE[(g, e)] = p(e|g); TEG[(e, g)] = p(g|e)
    json.dump({'ge': {'\t'.join(k): v for k, v in TGE.items()}, 'eg': {'\t'.join(k): v for k, v in TEG.items()}}, open(CACHE, 'w'))
def diag(i, m, j, n, lam=3.0): return math.exp(-lam * abs((i + .5) / m - (j + .5) / n))
def align(p):
    toks, ets = p[3], p[4]; m, n = len(toks), len(ets); out = [0] * m
    if not n: return out, {}
    es = [stem(e[2]) for e in ets]; efn = [e[2].lower() in EFUNC for e in ets]
    S = {}; rows = {}
    for i, t in enumerate(toks):
        code = MT[t[2]][0]
        if gfunc(code): continue          # content words only (nouns, verbs, adjectives, numerals); function words abstain
        g = str(t[1]); fn = False; row = []
        for j in range(n):
            if efn[j] and not fn: row.append(0.0); continue
            a = TGE.get((g, es[j]), 0.0); b = TEG.get((es[j], g), 0.0)
            s = math.sqrt(a * b) * diag(i, m, j, n) * (3.0 if es[j] in GL[g] else 1.0)
            row.append(s)
        z = sum(row) + 1e-3
        rows[i] = (row, z)
        for j, s in enumerate(row):
            if s > 0: S[(i, j)] = s
    used_e = set(); used_g = set(); conf = {}
    for (i, j), s in sorted(S.items(), key=lambda kv: -kv[1]):
        if i in used_g or j in used_e: continue
        c = s / rows[i][1]
        if c < 0.15: continue
        tk = toks[i]; g = str(tk[1])
        if GFREQ[g] < RARE and es[j] not in GL[g] and not (tk[0][:1].isupper() and ets[j][2][:1].isupper()) and c < RARE_CONF: continue
        used_g.add(i); used_e.add(j); conf[i] = (j, c)
    for i, (j, c) in conf.items():
        out[i] = [ets[j][0], ets[j][1], round(100 * c)]
    return out, conf
if __name__ == '__main__':
    import shutil
    if '--sample' in sys.argv:
        N = int(sys.argv[sys.argv.index('--sample') + 1]); rnd = random.Random(31)
        rows = []
        while len(rows) < N:
            p = rnd.choice(pairs); out, _ = align(p)
            i = rnd.randrange(len(p[3])); t = p[3][i]
            if gfunc(MT[t[2]][0]): continue
            o = out[i]; w = p[5][o[0]:o[1]] if o else ''
            ctx = (p[5][:o[0]] + '[[' + w + ']]' + p[5][o[1]:]) if o else p[5]
            rows.append([f'{p[0]} {p[1]}:{p[2]}', t[0], LEX[str(t[1])][1], MT[t[2]][0], w, o[2] if o else 0, ctx, ' '.join(x[0] for x in p[3])])
        with open(os.path.join(HERE, 'brentalign_sample.tsv'), 'w') as f:
            for r in rows: f.write('\t'.join(map(str, r)) + '\n')
        sys.exit()
    shutil.rmtree(D + '/bw', ignore_errors=True); tot = shown = 0
    by = collections.defaultdict(dict)
    for p in pairs:
        out, _ = align(p); out = [o if (o and o[2] >= THRESH * 100) else 0 for o in out]
        if any(out): by[(p[0], p[1])][p[2]] = out
        tot += sum(1 for t in p[3] if not gfunc(MT[t[2]][0])); shown += sum(1 for o in out if o)
    for (b, c), d in by.items():
        os.makedirs(f'{D}/bw/{b}', exist_ok=True); json.dump(d, open(f'{D}/bw/{b}/{c}.json', 'w'), separators=(',', ':'))
    print(f'brentalign: threshold {THRESH}: linked {shown}/{tot} content-word tokens ({100*shown/tot:.1f}%)')

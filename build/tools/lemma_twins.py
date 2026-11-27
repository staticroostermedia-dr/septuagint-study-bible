#!/usr/bin/env python3
"""Greek Maestro's calls on the 13 same-spelling headword pairs left by lemma_merge_nt.py (run after it; idempotent; run in site/,
then forms_fold.py and pwa.py). `--review` only rewrites build/lemma_twins_review.tsv.

MERGE (old ids redirect, like lemma_merge_nt.py): ἅπτω (NT 'kindle' entry into the LXX one); the three ἔπω entries; and the NT twins
whose right entry already exists under the correct headword: NT 'εἴδω' (οἶδα forms, G6063/G2467) -> οἶδα; NT 'εἴκω' (ἔοικεν, Jas 1:6,23)
-> ἔοικα; NT 'ἀνάθεμα' (ἀναθήμασιν, Luke 21:5) -> ἀνάθημα; χράομαι (EpJer 1:59) -> the χράομαι 'use' entry (formerly headed χράω).
SPLIT OUT: τυπικῶς (1 Cor 10:11) and ἀπασπάζομαι (Acts 21:6) already had their own entries under the wrong headword -> renamed;
no other token moves. The LXX 'εἴδω' entry held both εἶδον 'see' and οἶδα 'know' forms: tokens tagged perfect, pluperfect or future
move to οἶδα; the aorist forms stay and the entry is headed εἶδον, cross-linked to ὁράω.
KEEP SEPARATE with distinguishing glosses (hand-written, original wording kept under Other meanings): μή/μήτι, μακρός/μακράν,
χράομαι/χράω, ἀνάθεμα/ἀνάθημα, ἄπειμι ×2, σύνειμι ×2, βάτος ×2, εἴκω/ἔοικα.
Lexicon field 9 (new, optional) = ids of cross-linked entries, shown as 'See also' on the card, the occurrence page and search rows.
Tokens that do not fit a split are NOT moved; they are listed in build/lemma_twins_review.tsv for Greek Maestro.

ROUND 2 (Greek Maestro's rulings on the 142 review rows; RULINGS below; every move/flag is logged in build/lemma_twins_rulings.tsv):
1 μήτι under μή -> μήτι. 2 the exact form μακράν/μακρὰν under μακρός -> μακράν (adverb), except where it agrees with the feminine
accusative singular noun right before it (ὁδὸν/χώραν/γῆν μακράν): those stay under μακρός and are flagged. 3 active forms under
χράομαι -> χράω 'lend' when clearly active by form and sense (ἔχρησαν, ἔχρησας, χρήσωμεν); χρῆσαι (Jdt 3:2-3) is read as the
aorist middle imperative 'use (us)' and stays, flagged. 4 εἶμι forms of ἄπειμι (ἀπῄει/ἀπήει, ἀπῄεσαν, ἀπι-) -> the ἄπειμι (εἶμι)
'go away, depart' entry (the NT Acts 17:10 entry, now LXX + NT); ἀπών, ἀπεῖναι, ἄπεστι... stay 'be absent'. 5 συνι- participles
under σύνειμι 'be with' -> συνίημι (existing entry); the forms are shared with σύνειμι (εἶμι) (cf. Luke 8:4), context decides.
6 βατῶν (2 Esdr 7:22) -> the NT ὁ βάτος 'bath' entry (Luke 16:6)."""
import json, os, glob, re, sys, unicodedata, collections
D = 'data'
def jl(p): return json.load(open(p, encoding='utf-8'))
def jd(o, p): json.dump(o, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
L = jl(f'{D}/lexicon.json'); MORPH = jl(f'{D}/morph.json'); BOOKS = jl(f'{D}/books.json')
NTB = {b['id'] for b in BOOKS if b.get('nt')}; ORDER = {b['id']: i for i, b in enumerate(BOOKS)}
MERGE = [('10060', '465'), ('9993', '10054'), ('9997', '10054'), ('10044', '1168'), ('10749', '1168'), ('11353', '5369'), ('10420', '4513'), ('16507', '928')]
# id: (headword, translit, beta, POS, gloss, crosslinks)  -- None keeps the field
LABEL = {
    '465':   ('ἅπτω', 'haptō', None, 'Verb', 'touch (mid.); kindle (act.)', None),
    '10054': ('ἔπω', 'epō', None, 'Verb', 'say (ἐρῶ future, εἶπον aorist: forms of λέγω)', ['31']),
    '10962': ('τυπικῶς', 'tupikōs', 'tupikw=s', 'Adverb', 'as an example', None),
    '10720': ('ἀπασπάζομαι', 'apaspazomai', 'a)paspa/zomai', 'Verb', 'say farewell', None),
    '25':    (None, None, None, None, 'not', None),
    '10058': ('μήτι', 'mēti', 'mh/ti', 'Particle', "question particle expecting 'no' (surely not …?)", ['25']),
    '642':   (None, None, None, 'Adjective', 'long, far', None),
    '10068': ('μακράν', 'makran', 'makra/n', 'Adverb', 'far away', ['642']),
    '928':   ('χράομαι', 'chraomai', 'xra/omai', 'Verb', 'use', None),
    '10376': ('χράω', 'chraō', 'xra/w', 'Verb', 'lend', ['928']),
    '1695':  (None, None, None, None, 'curse, thing devoted to destruction', None),
    '4513':  (None, None, None, None, 'votive offering', None),
    '2818':  (None, None, None, 'Verb', 'be absent (from εἰμί)', None),
    '10642': (None, None, 'a)/peimi', 'Verb', 'go away (from εἶμι)', None),
    '2291':  (None, None, None, 'Verb', 'be with (from εἰμί)', None),
    '10359': (None, None, 'su/neimi', 'Verb', 'come together (from εἶμι)', None),
    '2872':  (None, None, None, None, 'thornbush (ἡ βάτος)', None),
    '10394': (None, None, 'ba/tos', None, 'bath, a liquid measure (ὁ βάτος)', None),
    '5610':  (None, None, None, None, 'yield, give way', None),
    '5369':  ('ἔοικα', 'eoika', 'e)/oika', 'Verb', 'be like, resemble', None),
    '53':    ('εἶδον', 'eidon', 'ei)=don', 'Verb', 'saw, see (aorist; present ὁράω)', ['112']),
    '1168':  (None, None, None, None, 'know (perfect οἶδα)', None),
}
LABEL.update({
    '10642': (None, None, 'a)/peimi', 'Verb', 'go away, depart (from εἶμι)', None),
    '10394': (None, None, 'ba/tos', None, 'bath, a liquid measure from Hebrew (ὁ βάτος)', None),
})
def NFC(x): return unicodedata.normalize('NFC', x)
FEM_ACC_NOUN = re.compile(r'^noun: accusative singular feminine')
# (from id, to id, test(form, tag, ctx) -> 'move' | 'flag' | None, note); ctx = (previous token's tag, next token's form, next token's tag)
def agrees(ctx):   # μακράν right after a fem. acc. sg. noun, and not itself governing ἀπό or a finite verb (λύπην μακρὰν ἀπόστησον, Sir 30:23)
    pt, nf, nt = ctx
    return bool(FEM_ACC_NOUN.match(pt)) and not NFC(nf.lower()).startswith((NFC('ἀπό'), NFC('ἀπ'), NFC('ἀφ'))) and not re.search(r'indicative|imperative|subjunctive|optative', nt)
RULINGS = [
    ('25', '10058', lambda f, t, pt: 'move' if NFC(f.lower()).startswith('μήτι') else None, '1 μήτι'),
    ('642', '10068', lambda f, t, pt: None if NFC(f.lower()) not in (NFC('μακρὰν'), NFC('μακράν')) else ('flag' if agrees(pt) else 'move'),
     '2 μακράν: adverbial -> μακράν; flag = agrees with the feminine accusative noun before it, kept under μακρός'),
    ('928', '10376', lambda f, t, pt: None if ' active ' not in t else ('flag' if NFC(f.lower()) == NFC('χρῆσαι') else 'move'),
     "3 active χράω 'lend'; flag = χρῆσαι: tagged aor. act. inf., but with dative ('use us') read as aor. mid. imperative 2sg of χράομαι, kept"),
    ('2818', '10642', lambda f, t, pt: 'move' if re.match(NFC(r'^(ἀπῄει|ἀπήει|ἀπῄεσ|ἀπήεσ|ἀπιών|ἀπιὼν|ἀπιόντ|ἀπιοῦσ|ἀπιέναι)'), NFC(f.lower())) else None, "4 εἶμι form -> ἄπειμι 'go away'"),
    ('2291', '606', lambda f, t, pt: 'move' if re.match(NFC(r'^συνι(ών|ὼν|όντ|οῦσ)'), NFC(f.lower())) else None,
     "5 συνι- participle -> συνίημι 'understand' (form shared with σύνειμι 'come together'; context: understanding)"),
    ('2872', '10394', lambda f, t, pt: 'move' if NFC(f).startswith('βατῶν') else None, "6 βατῶν 'baths' -> ὁ βάτος"),
]
RULE_LOG = []
ADVERB = next(i for i, m in enumerate(MORPH) if m[1] == 'adverb')
SEE_TO_KNOW = ('53', '1168')     # tokens tagged perfect / pluperfect / future move from εἶδον to οἶδα
def tense(mi): t = MORPH[mi][1] if mi is not None and mi < len(MORPH) else ''; return t
def is_know(mi): return bool(re.search(r'\b(perfect|pluperfect|future)\b', tense(mi)))
def chapters():
    for b in BOOKS:
        for c in b['chapters']:
            f = f'{D}/{b["id"]}/{c}.json'
            if os.path.exists(f): yield b['id'], c, f
# tokens that don't fit the split: (entry id, test(form, tag), note); listed, never moved
REVIEW = [
    ('25', lambda f, t: f.lower().startswith('μήτι'), 'μήτι form under μή'),
    ('642', lambda f, t: NFC(f.lower()).rstrip() in (NFC('μακρὰν'), NFC('μακράν')), 'μακράν kept under μακρός: agrees with the feminine accusative noun before it (ruling 2)'),
    ('928', lambda f, t: ' active ' in t, "χρῆσαι kept under χράομαι: read as aor. mid. imperative 'use (us)' (ruling 3)"),
    ('2818', lambda f, t: f.startswith(('ἀπῄ', 'ἀπι', 'ἀπί')), "εἶμι form ('go away') under ἄπειμι 'be absent'"),
    ('2291', lambda f, t: f.lower().startswith(('συνι', 'συνί')), "συνι- form under σύνειμι 'be with'"),
    ('2872', lambda f, t: f.startswith('βατῶν'), "'bath' measure (ὁ βάτος) under 'thornbush'"),
    ('10054', lambda f, t: True, "future ἐρῶ forms: the requested gloss 'said (aorist of λέγω)' does not fit; gloss written as future + aorist"),
]
def review():
    rows = []
    for b, c, f in chapters():
        for v in jl(f):
            for w in v[1]:
                for lid, test, note in REVIEW:
                    if str(w[1]) == lid and test(w[0], tense(w[2])): rows.append((lid, L[lid][0], w[0], tense(w[2]), f'{b} {c}:{v[0]}', note))
    with open('build/lemma_twins_review.tsv', 'w', encoding='utf-8') as o:
        o.write('entry\theadword\tform\ttag\tref\tnote\n')
        for r in rows: o.write('\t'.join(map(str, r)) + '\n')
    return rows
if '--review' in sys.argv:
    print(collections.Counter((r[1], r[5][:40]) for r in review())); sys.exit()
RED = jl(f'{D}/lexredirect.json'); st = collections.Counter()
todo = [(s, t) for s, t in MERGE if s in L]
M = {int(s): int(t) for s, t in todo}
touched = {int(x) for x in LABEL} | {int(s) for s, t in MERGE} | {int(t) for s, t in MERGE} | {int(r[0]) for r in RULINGS} | {int(r[1]) for r in RULINGS}
RULE = {int(r[0]): r for r in RULINGS}
for b, c, f in chapters():                       # token moves: merges + εἶδον/οἶδα split
    vs = jl(f); ch = 0
    for v in vs:
        for w in v[1]:
            if w[1] in M: w[1] = M[w[1]]; ch += 1; st['merge_tokens'] += 1
            elif w[1] == int(SEE_TO_KNOW[0]) and is_know(w[2]): w[1] = int(SEE_TO_KNOW[1]); ch += 1; st['eidon_to_oida_' + ('NT' if b in NTB else 'LXX')] += 1
        for i, w in enumerate(v[1]):                 # round 2 rulings
            r = RULE.get(w[1])
            if not r: continue
            pt = (tense(v[1][i - 1][2]) if i else '', v[1][i + 1][0] if i + 1 < len(v[1]) else '', tense(v[1][i + 1][2]) if i + 1 < len(v[1]) else '')
            d = r[2](w[0], tense(w[2]), pt)
            if d == 'move':
                RULE_LOG.append(('moved', r[0], r[1], w[0], tense(w[2]), f'{b} {c}:{v[0]}', r[3])); w[1] = int(r[1]); ch += 1; st['ruling_' + r[3][:1]] += 1
                if r[1] == '10068' and MORPH[w[2]][1].startswith('adjective'): w[2] = ADVERB   # tagged like the NT μακράν tokens
            elif d == 'flag': RULE_LOG.append(('flagged', r[0], r[0], w[0], tense(w[2]), f'{b} {c}:{v[0]}', r[3] + ' | context: ' + ' '.join(x[0] for x in v[1][max(0, i - 2):i + 2])))
    if ch: jd(vs, f)
for f in glob.glob(f'{D}/wk/*/*.json'):
    d = jl(f); ch = 0
    for vn in d.values():
        for i, x in vn.items():
            if int(x[0]) in M: x[0] = M[int(x[0])]; ch += 1
    if ch: jd(d, f); st['wk_links'] += ch
for s, t in todo:
    for k, v in list(RED.items()):
        if v == s: RED[k] = t
    RED[s] = t; del L[s]; st['merged'] += 1
for lid, (hw, tr, beta, pos, gloss, xref) in LABEL.items():
    v = L[lid]
    while len(v) < 9: v.append([] if len(v) >= 7 else '')
    if hw and v[0] != hw:
        if v[0] not in v[8] and lid in ('5369',): v[8].append(v[0])
        v[0] = hw
    if tr: v[3] = tr
    if beta: v[4] = beta
    if pos: v[2] = pos
    if gloss and v[1] != gloss:
        if v[1] and not any(x[0] == v[1] for x in v[7]): v[7].insert(0, [v[1], v[6] or 'T'])
        v[1], v[6] = gloss, 'W'
    if xref is not None:
        while len(v) < 10: v.append([])
        v[9] = xref
    st['labelled'] += 1
# recount every touched entry from the chapter tokens (same formats as build_clean.py / nt_counts.py)
cnt = {'L': collections.Counter(), 'N': collections.Counter()}; occ = {'L': collections.defaultdict(list), 'N': collections.defaultdict(list)}
forms = {'L': collections.defaultdict(collections.OrderedDict), 'N': collections.defaultdict(collections.OrderedDict)}; bk = collections.defaultdict(collections.Counter)
for b, c, f in chapters():
    side = 'N' if b in NTB else 'L'
    for v in jl(f):
        seen = set()
        for w in v[1]:
            if w[1] not in touched: continue
            lid = w[1]; cnt[side][lid] += 1; bk[lid][b] += 1; fk = (w[0], w[2]); fo = forms[side][lid]
            if fk not in fo: fo[fk] = [w[0], w[2], 0, f'{b}|{c}|{v[0]}']
            fo[fk][2] += 1
            if lid not in seen: seen.add(lid); occ[side][lid].append(f'{b}|{c}|{v[0]}')
C, N, NT, HIDE = jl(f'{D}/counts.json'), jl(f'{D}/ntcounts.json'), jl(f'{D}/nt.json'), jl(f'{D}/lexhide.json')
FB, OB, ONB = {}, {}, {}
def bucket(cache, sub, n):
    if n not in cache: p = f'{D}/{sub}/{n}.json'; cache[n] = jl(p) if os.path.exists(p) else {}
    return cache[n]
for lid in touched:
    k = str(lid); n = lid // 100; alive = k in L
    for side, CC, sub, cache in (('L', C, 'occ', OB), ('N', N, 'occnt', ONB)):
        o = bucket(cache, sub, n)
        if alive and cnt[side][lid]: CC[k] = cnt[side][lid]; o[k] = [cnt[side][lid]] + occ[side][lid]
        else: CC.pop(k, None); o.pop(k, None)
    fb = bucket(FB, 'forms', n)
    if alive and (cnt['L'][lid] or cnt['N'][lid]):
        e = {'f': sorted(forms['L'][lid].values(), key=lambda x: -x[2]), 'b': dict(bk[lid])}
        if cnt['N'][lid]: e['nf'] = sorted(forms['N'][lid].values(), key=lambda x: -x[2])
        fb[k] = e
    else: fb.pop(k, None)
    if alive and cnt['N'][lid] and (k in NT or cnt['L'][lid]): NT[k] = [cnt['N'][lid]] + ['%s %s:%s' % tuple(r.split('|')) for r in occ['N'][lid][:3]]   # nt.json keeps the count + first 3 refs (nt_counts.py)
    elif not alive or not cnt['N'][lid]: NT.pop(k, None)
    if not alive: HIDE = [x for x in HIDE if str(x) != k]
for sub, cache in (('forms', FB), ('occ', OB), ('occnt', ONB)):
    for n, d in cache.items(): jd(d, f'{D}/{sub}/{n}.json')
jd(C, f'{D}/counts.json'); jd(N, f'{D}/ntcounts.json'); jd(NT, f'{D}/nt.json'); jd(HIDE, f'{D}/lexhide.json')
json.dump(RED, open(f'{D}/lexredirect.json', 'w')); jd(L, f'{D}/lexicon.json')
a = open('app.js', encoding='utf-8').read()
a = re.sub(r'var LEXRED = \{[^}]*\};', lambda m: 'var LEXRED = ' + json.dumps(RED, separators=(',', ':')) + ';', a, count=1)
open('app.js', 'w', encoding='utf-8').write(a)
RP = 'build/lemma_twins_rulings.tsv'          # moves are logged once (a rerun finds nothing left to move); flags are rewritten
old = [l.rstrip('\n').split('\t') for l in open(RP, encoding='utf-8')][1:] if os.path.exists(RP) else []
rows = [tuple(r) for r in old if r[0] == 'moved'] + [r for r in RULE_LOG if r[0] == 'moved'] + [r for r in RULE_LOG if r[0] == 'flagged']
with open(RP, 'w', encoding='utf-8') as o:
    o.write('action\tfrom\tto\tform\ttag\tref\tnote\n')
    for r in rows: o.write('\t'.join(map(str, r)) + '\n')
rv = review()
print(dict(st), 'merged:', todo, 'review rows:', len(rv))

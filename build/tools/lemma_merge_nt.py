#!/usr/bin/env python3
"""Merge NT-only duplicate headwords into the main (LXX+NT) entry with the same dictionary form. Idempotent; run in site/.

Why: build_nt.py keys NT lemmas by TAGNT Strong's number. Where TAGNT splits one dictionary word over two numbers (e.g. ἅγιος
G0040 'holy' and G0039 'holy place' = τὸ ἅγιον / τὰ ἅγια), the second number became a separate lexicon entry with the SAME headword.
Its words were counted only there, so the word card, counts and occurrence list (#/search?lex=) of the duplicate show just those
few NT verses (ἅγιος G0039: 11 hits, all Hebrews, 0 LXX), and the main entry misses them. Search lists two identical-looking ἅγιος rows.

Only the reviewed pairs in MERGE are merged: the duplicate's words are plain inflections of the main headword. Every word keeps its own
form and grammar tag. Homographs that are different words (μήν 'month'/'indeed', βάτος 'bush'/'bath', ἄπειμι 'be away'/'go', ...)
and doubtful pairs are NOT merged; build/tools/lemma_merge_nt.py --report lists every remaining same-headword pair.
Updates: chapter token lex ids, data/wk links, lexicon.json, counts.json, ntcounts.json, nt.json, occ/, occnt/, forms/, lexhide.json,
lexredirect.json and the LEXRED copy inlined in app.js (old ids keep working as links/bookmarks). Then run pwa.py."""
import json, os, glob, re, sys, unicodedata, collections
D = 'data'; NFC = lambda s: unicodedata.normalize('NFC', s)
# (duplicate id, main id, headword) - duplicate's TAGNT number in the comment
MERGE = [
    ('11330', '75', 'ἅγιος'),       # G0039 τὸ ἅγιον / τὰ ἅγια (Heb) -> G0040
    ('9994', '6', 'ἐγώ'),           # G3165 μου/με/μοι/ἡμῶν/ἡμῖν/ἡμᾶς -> G1473
    ('10135', '10', 'εἰμί'),        # G1511 εἶναι -> G1510
    ('10014', '255', 'σεαυτοῦ'),    # G4771-tagged σεαυτόν/-ῷ/-οῦ
    ('10049', '441', 'πως'),        # G4459 πῶς -> the LXX πῶς entry
    ('10146', '525', 'ἐμός'),       # G1473-tagged ἐμός forms
    ('10000', '613', 'κἀγώ'),       # G1473-tagged κἀγώ/κἀμοί/κἀμέ
    ('10053', '405', 'σός'),        # G4771-tagged σός forms
    ('10062', '890', 'ἐμαυτοῦ'),    # G1473-tagged ἐμαυτοῦ forms
    ('10015', '964', 'μήποτε'),     # G3361-tagged μήποτε
    ('10505', '1712', 'ἡμέτερος'),  # G1473-tagged ἡμέτερος forms
    ('10347', '4651', 'ὑμέτερος'),  # G4771-tagged ὑμέτερος forms
    ('10608', '10122', 'κἀκεῖνος'), # G1565-tagged κἀκεῖνοι
    ('10160', '2090', 'κἄν'),       # G2532-tagged κἄν
    ('10101', '3204', 'ἔξεστι'),    # G1832 ἔξεστιν/ἐξόν
    ('10346', '3057', 'ζηλωτής'),   # G2208 ζηλωτής (Simon the Zealot)
    ('10318', '472', 'σωτήριον'),   # G4991-tagged σωτήριον
    ('10255', '7539', 'κἀκεῖθεν'),  # G2532-tagged κἀκεῖθεν
    ('10711', '9184', 'ἄντικρυς'),  # G0481 ἄντικρυς (Acts 20:15)
    ('11390', '10715', 'ταπεινοφροσύνη'),  # G9402-tagged ταπεινοφροσύνη
]
def jl(p): return json.load(open(p, encoding='utf-8'))
def jd(o, p): json.dump(o, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
L = jl(f'{D}/lexicon.json')
if '--report' in sys.argv:
    C, N = jl(f'{D}/counts.json'), jl(f'{D}/ntcounts.json'); g = collections.defaultdict(list)
    for k, v in L.items(): g[NFC(v[0])].append(k)
    for h, ks in sorted(g.items(), key=lambda x: -sum(C.get(k, 0) + N.get(k, 0) for k in x[1])):
        if len(ks) > 1: print(h, [(k, L[k][2], L[k][5] if len(L[k]) > 5 else '', C.get(k, 0), N.get(k, 0), L[k][1][:30]) for k in ks])
    sys.exit()
books = jl(f'{D}/books.json'); NTB = {b['id'] for b in books if b.get('nt')}; ORDER = {b['id']: i for i, b in enumerate(books)}
RED = jl(f'{D}/lexredirect.json') if os.path.exists(f'{D}/lexredirect.json') else {}
todo = []
for s, t, h in MERGE:
    if s not in L: continue                                   # already merged
    assert t in L and NFC(L[s][0]) == NFC(h) == NFC(L[t][0]), (s, t, h)
    todo.append((s, t))
st = collections.Counter()
if todo:
    M = {int(s): int(t) for s, t in todo}
    for f in glob.glob(f'{D}/*/*.json'):                      # chapter files: [[v, [[form, lex, morph], ...], ...], ...]
        b = f.split('/')[1]
        if b not in ORDER: continue
        vs = jl(f); ch = 0
        for v in vs:
            for w in v[1]:
                if w[1] in M: w[1] = M[w[1]]; ch += 1
        if ch: jd(vs, f); st['words_NT' if b in NTB else 'words_LXX'] += ch
    for f in glob.glob(f'{D}/wk/*/*.json'):                   # Wiktionary-layer links
        d = jl(f); ch = 0
        for vn in d.values():
            for i, x in vn.items():
                if int(x[0]) in M: x[0] = M[int(x[0])]; ch += 1
        if ch: jd(d, f); st['wk_links'] += ch
    def refkey(r):
        p = r.split('|'); return (ORDER.get(p[0], 999), [int(x) if x.isdigit() else 0 for x in p[1:]])
    def merge_occ(sub, s, t):                                 # [count, 'Book|ch|v', ...]
        sb, tb = int(s) // 100, int(t) // 100
        fs, ft = f'{D}/{sub}/{sb}.json', f'{D}/{sub}/{tb}.json'
        S = jl(fs) if os.path.exists(fs) else {}; T = S if sb == tb else (jl(ft) if os.path.exists(ft) else {})
        o = S.pop(s, None)
        if not o: return
        e = T.get(t, [0]); refs = sorted(set(e[1:]) | set(o[1:]), key=refkey)
        T[t] = [e[0] + o[0]] + refs; jd(S, fs)
        if T is not S: jd(T, ft)
        st[sub + '_merged'] += 1
    def merge_forms(s, t):
        sb, tb = int(s) // 100, int(t) // 100
        S = jl(f'{D}/forms/{sb}.json'); T = S if sb == tb else jl(f'{D}/forms/{tb}.json')
        o = S.pop(s, None)
        if o:
            e = T.setdefault(t, {'f': [], 'b': {}})
            for key in ('f', 'nf'):                           # [form, morph, count, firstRef]
                if not o.get(key): continue
                cur = e.setdefault(key, []); ix = {(x[0], x[1]): x for x in cur}
                for x in o[key]:
                    y = ix.get((x[0], x[1]))
                    if y: y[2] += x[2]; y[3] = min(y[3], x[3], key=refkey)
                    else: cur.append(list(x)); ix[(x[0], x[1])] = cur[-1]
                cur.sort(key=lambda x: -x[2])
            for b, n in o.get('b', {}).items(): e.setdefault('b', {})[b] = e['b'].get(b, 0) + n
            jd(S, f'{D}/forms/{sb}.json')
            if T is not S: jd(T, f'{D}/forms/{tb}.json')
    C, N, NT = jl(f'{D}/counts.json'), jl(f'{D}/ntcounts.json'), jl(f'{D}/nt.json')
    HIDE = jl(f'{D}/lexhide.json')
    for s, t in todo:
        merge_occ('occ', s, t); merge_occ('occnt', s, t); merge_forms(s, t)
        if s in C: C[t] = C.get(t, 0) + C.pop(s)
        if s in N: N[t] = N.get(t, 0) + N.pop(s)
        if s in NT or t in NT:                                # 'Also in the NT' list: [count, 'Book c:v', ...] rebuilt from occnt
            o = jl(f'{D}/occnt/{int(t) // 100}.json').get(t, [0])
            NT.pop(s, None); NT[t] = [N.get(t, 0)] + ['%s %s:%s' % tuple(r.split('|')) for r in o[1:4]]   # count + first 3 refs, like nt_counts.py
        HIDE = [x for x in HIDE if str(x) != s]
        for k, v in list(RED.items()):
            if v == s: RED[k] = t
        RED[s] = t; del L[s]; st['merged'] += 1
    jd(C, f'{D}/counts.json'); jd(N, f'{D}/ntcounts.json'); jd(NT, f'{D}/nt.json'); jd(HIDE, f'{D}/lexhide.json')
    json.dump(RED, open(f'{D}/lexredirect.json', 'w')); jd(L, f'{D}/lexicon.json')
    a = open('app.js', encoding='utf-8').read()
    a2 = re.sub(r'var LEXRED = \{[^}]*\};', lambda m: 'var LEXRED = ' + json.dumps(RED, separators=(',', ':')) + ';', a, count=1)
    assert a2 != a or 'var LEXRED = ' + json.dumps(RED, separators=(',', ':')) in a
    open('app.js', 'w', encoding='utf-8').write(a2)
print(dict(st), 'merged pairs:', todo)

#!/usr/bin/env python3
"""Add the NA28 words that build_nt.py used to drop (TAGNT gives them only in its variant column; see tagnt_na28.py) to the NT chapter
files in place, without a from-scratch NT rebuild (a full rebuild would lose later hand passes on NT tokens, e.g. the 2026-11-15 grammar pass).
Each verse is changed only if its words are exactly TAGNT's NA28 words minus the variant-column ones; the missing words are inserted at
TAGNT's position, as [form, lexicon id, grammar index] like every other token. The lexicon id is found as build_nt.py does (same Strong's
number and the same headword or an -ω/-ομαι/-μι variant of it), then followed through data/lexredirect.json; a new entry (with its
Abbott-Smith tab from TBESG) is made only if none exists. Idempotent. Writes build/nt_english/na28_variant_tokens.tsv (one row per word).
Run in site/, then: nt_lemmas.py, lemma_middle.py, nt_counts.py, lemma_merge_nt.py, lemma_twins.py, forms_fold.py,
na28_variant_tokens.py --ntjson (refresh 'Also in the NT' for the lemmas that gained words), nt_translit.py TBESG, nt_english_review.py,
build_votd.py, pwa.py."""
import json, os, re, sys, unicodedata, collections, csv
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); import tagnt_na28 as T
D = 'data'; TBESG = '/workspace/lxx-audit/src/tbesg.txt'; LOG = 'build/nt_english/na28_variant_tokens.tsv'
src = open(os.path.join(HERE, 'build_nt.py'), encoding='utf-8').read()
argv = sys.argv; sys.argv = ['build_nt.py', T.TAG, '', '.']; exec(src[:src.index("lex = json.load")]); sys.argv = argv   # NT table, conv(), nrm(), PUN, POSN
def jl(p): return json.load(open(p, encoding='utf-8'))
def jd(o, p): json.dump(o, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
if '--ntjson' in sys.argv:
    NTJ, N, C = jl(f'{D}/nt.json'), jl(f'{D}/ntcounts.json'), jl(f'{D}/counts.json'); n = 0
    for r in csv.DictReader(open(LOG, encoding='utf-8'), delimiter='\t'):
        k = r['lexicon id']; o = jl(f'{D}/occnt/{int(k) // 100}.json').get(k)
        if o and (k in NTJ or C.get(k)):
            new = [N.get(k, o[0])] + ['%s %s:%s' % tuple(x.split('|')) for x in o[1:4]]
            if NTJ.get(k) != new: NTJ[k] = new; n += 1
    jd(NTJ, f'{D}/nt.json'); print('nt.json entries refreshed:', n); sys.exit()
lex, morph = jl(f'{D}/lexicon.json'), jl(f'{D}/morph.json'); RED = jl(f'{D}/lexredirect.json')
mi = {m[0]: i for i, m in enumerate(morph)}; bystrong = collections.defaultdict(list)
for k, v in lex.items(): bystrong[v[5]].append(k)
def STEM(x): return re.sub('(ομαι|υμι|μι|ω|ον|οσ)$', '', nrm(x))
new_entries = []
def lexid(strong, lemma, gloss, pos):
    base = re.match(r'G\d+', strong).group(0); base = 'G%04d' % int(base[1:])
    cands = bystrong.get(base, [])
    k = next((k for k in cands if nrm(lex[k][0]) == nrm(lemma)), None) or next((k for k in cands if STEM(lex[k][0]) == STEM(lemma)), None)
    seen = set()
    while k and k in RED and k not in seen: seen.add(k); k = str(RED[k])
    if k: return k
    k = str(max(int(x) for x in lex) + 1)
    lex[k] = [lemma, gloss, pos, '', '', base, 'T', [[gloss, 'T']]]; bystrong[base].insert(0, k); new_entries.append(k); return k
W = T.na28_words(); log = []; st = collections.Counter(); files = {}
# How the app already files TAGNT's words: (Strong's base, TAGNT lemma[, grammar]) -> lexicon ids of the app's tokens, learned from every verse
# whose words line up with TAGNT. This carries over the later headword work (nt_lemmas, lemma_middle, merges, twins, grammar pass) to the new words.
SEEN1, SEEN2 = collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)
def skey(strong, lemma): return ('G%04d' % int(re.match(r'G(\d+)', strong).group(1)), nrm(lemma.split(',')[0].strip()))
for (tb, c, v), ws in W.items():
    fp = f'{D}/{T2ID[tb]}/{c}.json'
    if fp not in files: files[fp] = jl(fp)
    main = [w for w in ws if w[5] == 'main']
    for row in files[fp]:
        if row[0] == str(v) and [t[0] for t in row[1]] == [w[0] for w in main]:
            for w, t in zip(main, row[1]):
                k = skey(w[1], w[3]); SEEN1[k + (morph[t[2]][0] if t[2] < len(morph) else '',)][t[1]] += 1; SEEN2[k][t[1]] += 1
def known(strong, lemma, sc):
    k = skey(strong, lemma)
    for d, kk in ((SEEN1, k + (sc,)), (SEEN2, k)):
        if d.get(kk): return str(d[kk].most_common(1)[0][0])
for (tb, c, v), ws in W.items():
    if not any(w[5] == 'variant' for w in ws): continue
    bid = T2ID[tb]; fp = f'{D}/{bid}/{c}.json'
    if fp not in files: files[fp] = jl(fp)
    rows = [r for r in files[fp] if r[0] == str(v)]
    if not rows: st['verse_missing'] += 1; print('! no verse', bid, c, v); continue
    row = rows[0]; have = [t[0] for t in row[1]]
    if have == [w[0] for w in ws]: st['already'] += 1; ref = f'{bid} {c}:{v}'
    elif have == [w[0] for w in ws if w[5] == 'main']:
        out, it = [], iter(row[1])
        for w in ws:
            if w[5] == 'main': out.append(next(it)); continue
            form, strong, code, lemma, gloss = w[:5]
            crasis = ' + ' in code; sc, desc = conv(code.split('=')[-1] if crasis else code)
            if sc and sc not in mi: mi[sc] = len(morph); morph.append([sc, desc])
            pos = POSN.get(sc.split('.')[0], '').split(' ')[0].capitalize() if sc else ''
            k = known(strong, lemma, sc) or lexid(strong, lemma.split(',')[0].strip(), gloss.split('/')[0], pos)
            out.append([form, int(k), mi.get(sc, 0)]); st['added'] += 1
        row[1] = out; st['verses_changed'] += 1
    else: st['mismatch'] += 1; print('! verse words differ from TAGNT beyond the variant column, left as is:', bid, c, v, have, [w[0] for w in ws]); continue
    for i, w in enumerate(ws):
        if w[5] == 'variant':
            t = row[1][i]; log.append({'ref': f'{bid} {c}:{v}', 'position': i + 1, 'form': w[0], 'strong': w[1], 'code': w[2], 'TAGNT lemma': w[3], 'gloss': w[4],
                                      'lexicon id': t[1], 'headword': lex[str(t[1])][0], 'new entry': 'yes' if str(t[1]) in new_entries else ''})
for fp, d in files.items(): jd(d, fp)
jd(lex, f'{D}/lexicon.json'); jd(morph, f'{D}/morph.json')
if new_entries:   # Abbott-Smith tab from TBESG, as build_nt.py
    tb = {}
    for line in open(TBESG, encoding='utf-8'):
        f = line.rstrip('\n').split('\t')
        if len(f) > 7 and re.match(r'^G\d{4}', f[0]) and f[0] == f[2]: tb.setdefault(f[0], f)
    for k in new_entries:
        e = tb.get(lex[k][5])
        if not e: continue
        fp = f'{D}/dict/{int(k) // 100}.json'; b = jl(fp) if os.path.exists(fp) else {}
        full = e[7].strip(); bs = [re.sub('<[^>]+>', '', x).strip(' ,;:') for x in re.findall(r'<b>(.*?)</b>', full)[1:]]
        bs = [x for x in bs if x and not re.search('[\u0370-\u03ff\u1f00-\u1fff]', x)][:8]
        b[k] = {'id': lex[k][5], 'g': e[6], 's': bs or [e[6]], 'lxx': '', 'full': full}; jd(b, fp)
if log or not os.path.exists(LOG):
    if st['added'] or not os.path.exists(LOG):
        w = csv.DictWriter(open(LOG, 'w', encoding='utf-8', newline=''), list(log[0]) if log else ['ref'], delimiter='\t', lineterminator='\n'); w.writeheader(); w.writerows(log)
print(dict(st), 'new lexicon entries:', [(k, lex[k][0], lex[k][5]) for k in new_entries])

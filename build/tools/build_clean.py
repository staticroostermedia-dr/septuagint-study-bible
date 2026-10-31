#!/usr/bin/env python3
"""CLEAN-LICENCE build (branch clean-license). Sources:
  Greek text: Brenton's Greek, eBible.org grcbrent (public domain)       English: Brenton, eBible.org eng-Brenton (public domain)
  Lemma/morphology: tools/analyze.py routes M/N (Morpheus, MPL-2.0, run locally), T (STEPBible TAGNT, CC BY 4.0), H (TBESG/TFLSJ/Dodson headwords)
  Separate CC BY-SA layer: K (Wiktionary form->lemma links) -> data/wk/<Book>/<ch>.json, applied by the app at display time.
No CCAT / CATSS / Rahlfs / eliranwong data is read by this script."""
import json, os, re, sys, math, collections, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from greek import *
import analyze as AN
W = '/workspace/lxx-cl/work'; D = '/workspace/lxx-cl/site/data'
A = json.load(open(W + '/analysis_raw.json')); K = json.load(open(W + '/analysis_wikt.json'))
G = vpl(GRC); E = vpl(ENG)
ORDER = [('GEN','Gen','Genesis'),('EXO','Exod','Exodus'),('LEV','Lev','Leviticus'),('NUM','Num','Numbers'),('DEU','Deut','Deuteronomy'),
 ('JOS','Josh','Joshua'),('JDG','Judg','Judges'),('RUT','Ruth','Ruth'),('1SA','1Sam','1 Kingdoms (1 Samuel)'),('2SA','2Sam','2 Kingdoms (2 Samuel)'),
 ('1KI','1Kgs','3 Kingdoms (1 Kings)'),('2KI','2Kgs','4 Kingdoms (2 Kings)'),('1CH','1Chr','1 Chronicles'),('2CH','2Chr','2 Chronicles'),
 ('1ES','1Esdr','1 Esdras'),('EZR','2Esdr','2 Esdras (Ezra–Nehemiah)'),('ESG','Esth','Esther'),('JDT','Jdt','Judith'),('TOB','Tob','Tobit'),
 ('1MA','1Macc','1 Maccabees'),('2MA','2Macc','2 Maccabees'),('3MA','3Macc','3 Maccabees'),('4MA','4Macc','4 Maccabees'),
 ('PSA','Ps','Psalms'),('PRM','PrMan','Prayer of Manasses'),('PRO','Prov','Proverbs'),('ECC','Eccl','Ecclesiastes'),('SOL','Song','Song of Songs'),
 ('JOB','Job','Job'),('WIS','Wis','Wisdom of Solomon'),('SIR','Sir','Sirach'),('HOS','Hos','Hosea'),('AMO','Amos','Amos'),('MIC','Mic','Micah'),
 ('JOE','Joel','Joel'),('OBA','Obad','Obadiah'),('JON','Jonah','Jonah'),('NAH','Nah','Nahum'),('HAB','Hab','Habakkuk'),('ZEP','Zeph','Zephaniah'),
 ('HAG','Hag','Haggai'),('ZEC','Zech','Zechariah'),('MAL','Mal','Malachi'),('ISA','Isa','Isaiah'),('JER','Jer','Jeremiah'),('BAR','Bar','Baruch'),
 ('LAM','Lam','Lamentations'),('EPJ','EpJer','Epistle of Jeremiah'),('EZE','Ezek','Ezekiel'),('SUS','Sus','Susanna'),('DNG','Dan','Daniel'),('BEL','Bel','Bel and the Dragon')]
# ---------------- 1. pairing / versification check ----------------
gk = collections.defaultdict(set); ek = collections.defaultdict(set)
for (b, c, v) in G: gk[b].add((c, v))
for (b, c, v) in E: ek[b].add((c, v))
pair = {'books': {}, 'greek_only': {}, 'english_only': {}, 'empty': []}
for code, bid, name in ORDER:
    go = sorted(gk[code] - ek[code]); eo = sorted(ek[code] - gk[code])
    pair['books'][bid] = [len(gk[code]), len(ek[code]), len(gk[code] & ek[code])]
    if go: pair['greek_only'][bid] = ['%d:%s' % x for x in go]
    if eo: pair['english_only'][bid] = ['%d:%s' % x for x in eo]
pair['english_books_not_in_greek'] = {b: len(ek[b]) for b in ek if b not in gk}
pair['greek_books_not_listed'] = [b for b in gk if b not in {o[0] for o in ORDER}]
pair['empty'] = ['%s %d:%s' % k for k, t in G.items() if not tokens(t)] + ['EN %s %d:%s' % k for k, t in E.items() if not t.strip()]
# ---------------- 2. lemma choice ----------------
TAGN = collections.defaultdict(collections.Counter)
for f, d in A.items():
    for lem, n in d.get('tag', {}).items(): TAGN[f][norm(lem)] += n
def lemma_groups(f, cap=False):
    d = A.get(f)
    if not d or 'a' not in d: return {}
    g = collections.defaultdict(list)
    rows = d['a'] + (d.get('ac', []) if cap else [])
    if not rows and d.get('ac'):   # only a capitalised (name) analysis, but the word is lower case in the text: use the lower-case lemma
        rows = [[r[0][:1].lower() + r[0][1:]] + r[1:] for r in d['ac']]
    for lem, pos, feats, stype, pen, tbpos in rows: g[lem].append((pos, feats, stype, pen, tbpos))
    # TAGNT (CC BY) spelling of the same form: a candidate in its own right (Morpheus sometimes gives only an Attic/poetic lemma, e.g. φάος for φῶς)
    for lem, n in d.get('tag', {}).items():
        dl = AN.dict_lemma(lem)
        if not any(norm(x) == norm(dl) for x in g): g[dl].append(('T', d['tagm'][lem], '', 0, ''))
    return g
# prior: lemma frequency over tokens whose form has a single candidate lemma
prior = collections.Counter()
for t in G.values():
    for w in tokens(t):
        g = lemma_groups(lower_form(w), is_cap(acute(w)))
        if len(g) == 1: prior[next(iter(g))] += 1
def best_lemma(f, cap=False):
    g = lemma_groups(f, cap)
    if not g: return None, []
    def sc(lem):
        an = g[lem]; s = 3 * math.log1p(TAGN[f].get(norm(lem), 0))
        s += 1.5 if AN.headword(lem) else -2
        s += 0.6 * math.log1p(prior[lem]) - min(a[3] for a in an)
        return s
    lem = max(sorted(g), key=sc)
    an = g[lem]; mp = min(a[3] for a in an)
    return lem, [a for a in an if a[3] == mp]
CASEP = 'NAGDV'; MOODP = 'IPNSDO'
def cands(lem, an):
    cs = []
    for pos, feats, stype, pen, tbpos in an:
        for c in ([rob2code(feats)] if pos == 'T' else AN.codes(pos, feats, stype, tbpos)):
            if c not in cs: cs.append(c)
    hw = AN.headword(lem); tb = hw[2] if hw else ''
    m = re.match(r'[GN]:N-([MFN])', tb or '')
    if m:   # nouns have a fixed gender: keep the dictionary's
        keep = [c for c in cs if not re.match(r'N\.[NGDAV][SPD][MFN]$', c) or c.endswith(m.group(1))]
        cs = keep or cs
    return cs
def cng(c):
    m = re.search(r'([NGDAV])([SPD])([MFN])$', c); return m.groups() if m else None
ROB = {'N': 'N', 'A': 'A', 'T': 'RA', 'P': 'RP', 'R': 'RR', 'D': 'RD', 'I': 'RI', 'Q': 'RI', 'X': 'RI', 'F': 'RP', 'S': 'A', 'K': 'RP', 'C': 'RP'}
def rob2code(r):
    r = r.split('-')
    if r[0] in ('PREP',): return 'P'
    if r[0] in ('CONJ', 'COND'): return 'C'
    if r[0] == 'ADV': return 'D'
    if r[0] in ('PRT', 'PRT'): return 'X'
    if r[0] in ('INJ', 'ARAM', 'HEB'): return 'I' if r[0] == 'INJ' else 'N'
    if r[0] == 'V' and len(r) > 1:
        t = r[1].lstrip('2'); 
        if len(t) >= 3:
            tm = {'P': 'P', 'I': 'I', 'F': 'F', 'A': 'A', 'R': 'X', 'L': 'Y'}.get(t[0], 'P'); vm = {'A': 'A', 'M': 'M', 'P': 'P', 'E': 'E', 'D': 'M', 'O': 'P', 'N': 'E'}.get(t[1], 'A')
            mm = {'I': 'I', 'S': 'S', 'O': 'O', 'M': 'D', 'N': 'N', 'P': 'P'}.get(t[2], 'I')
            if mm == 'P' and len(r) > 2 and len(r[2]) >= 3: return f'V.{tm}{vm}P{r[2][0]}{r[2][1]}{r[2][2]}'
            if mm == 'N': return f'V.{tm}{vm}N'
            if len(r) > 2 and len(r[2]) >= 2: return f'V.{tm}{vm}{mm}{r[2][0]}{r[2][1]}'
        return 'V'
    pre = ROB.get(r[0][0], 'N')
    if len(r) > 1 and re.match(r'^[1-3]?[NGDAV][SP][MFN]?$', r[1]):
        x = r[1].lstrip('123'); return f'{pre}.{x[0]}{x[1]}{x[2] if len(x) > 2 else ""}'
    return pre if pre != 'N' else 'N'
WKT = {'nominative': 'N', 'genitive': 'G', 'dative': 'D', 'accusative': 'A', 'vocative': 'V'}
def wk2code(pos, tags):
    t = set(tags)
    c = next((WKT[x] for x in tags if x in WKT), ''); n = 'P' if 'plural' in t else 'D' if 'dual' in t else 'S' if 'singular' in t else ''
    g = 'M' if 'masculine' in t else 'F' if 'feminine' in t else 'N' if 'neuter' in t else ''
    if pos == 'verb':
        tm = 'A' if 'aorist' in t else 'X' if 'perfect' in t else 'Y' if 'pluperfect' in t else 'F' if 'future' in t else 'I' if 'imperfect' in t else 'P'
        vm = 'P' if 'passive' in t else 'E' if 'mediopassive' in t else 'M' if 'middle' in t else 'A'
        if 'participle' in t: return f'V.{tm}{vm}P{c}{n}{g}' if c and n and g else 'V'
        if 'infinitive' in t: return f'V.{tm}{vm}N'
        mm = 'S' if 'subjunctive' in t else 'O' if 'optative' in t else 'D' if 'imperative' in t else 'I'
        pe = '1' if 'first-person' in t else '2' if 'second-person' in t else '3' if 'third-person' in t else ''
        return f'V.{tm}{vm}{mm}{pe}{n}' if pe and n else 'V'
    pre = {'noun': 'N', 'name': 'N', 'adj': 'A', 'pron': 'RP', 'num': 'M', 'adv': 'D', 'prep': 'P', 'conj': 'C', 'particle': 'X', 'intj': 'I', 'article': 'RA'}.get(pos, 'N')
    return f'{pre}.{c}{n}{g}' if c and n and pre in ('N', 'A', 'RP', 'RA') else pre
# ---------------- 3. assemble tokens ----------------
LEMMAS = {}; LSRC = collections.Counter(); TOKSRC = collections.Counter()
def lid(lem):
    if lem not in LEMMAS: LEMMAS[lem] = None
    return lem
verses = collections.OrderedDict()
for code, bid, name in ORDER:
    for (b, c, v), t in G.items():
        if b != code: continue
        verses.setdefault((bid, c), []).append((v, t))
chap = {}
for (bid, c), vs in verses.items():
    out = []
    for v, t in sorted(vs, key=lambda x: vkey(x[0])):
        ws = tokens(t); toks = []
        for i, w in enumerate(ws):
            f = lower_form(w); d = A.get(f); lem, cs, src = None, [], '-'
            if d and d['src'] in 'MN':
                lem, an = best_lemma(f, is_cap(acute(w)))
                if lem:
                    cs = cands(lem, an); src = d['src']
                    tm = next((rob2code(m) for l, m in d.get('tagm', {}).items() if norm(AN.dict_lemma(l)) == norm(lem)), None)
                    if tm in cs: cs = [tm] + [c for c in cs if c != tm]   # same form+lemma in TAGNT: its parse first
                    elif tm: cs = sorted(cs, key=lambda c: -sum(a == b for a, b in zip(c, tm)))
            elif d and d['src'] == 'T':
                lem = d['tagnt'][0]; cs = [rob2code(d['tagnt'][1])]; src = 'T'
                if norm(f) in [norm(x) for x in lem.split(', ')]: cs = [cs[0].split('.')[0]]   # uninflected (often indeclinable names): no case shown
            elif d and d['src'] == 'H':
                lem = d['hw'][0]; tb = d['hw'][1] or ''
                cs = ['V' if tb.startswith('G:V') else 'A' if tb.startswith('G:A') else 'D' if 'ADV' in tb else 'N']; src = 'H'
            elif f in K:
                lem = K[f]['wk'][0]; cs = [wk2code(K[f]['wk'][1], K[f]['wk'][2])]; src = 'K'
            if lem: lem = AN.dict_lemma(lem)
            toks.append([w, lem, cs, src, bool(d and d.get('tagm') and lem and any(norm(AN.dict_lemma(l)) == norm(lem) for l in d['tagm']))])
            TOKSRC[src] += 1
        out.append([v, toks, E.get((next(o[0] for o in ORDER if o[1] == bid), c, v))])
    chap[(bid, c)] = out
# context choice of the morphology code (agreement with neighbours; preference order otherwise)
def pref(c):
    x = cng(c)
    if x: return CASEP.index(x[0]) * 10 + 'SPD'.index(x[1])
    m = re.match(r'V\.([PIFAXY])([AMPE])([ISODNP])(\d?)', c)
    return MOODP.index(m.group(3)) * 100 + '3120'.index(m.group(4) or '0') * 10 + 'AMEP'.index(m.group(2)) if m else 0
for key, vs in chap.items():
    for v in vs:
        toks = v[1]
        for i, t in enumerate(toks):
            cs = t[2]
            if len(cs) <= 1: t[2] = cs[0] if cs else ''; continue
            def agree(c):
                x = cng(c)
                if not x: return 0
                s = 0
                for j in (i - 2, i - 1, i + 1, i + 2):
                    if 0 <= j < len(toks):
                        o = toks[j][2]; o = o if isinstance(o, list) else [o]
                        ys = [cng(z) for z in o if cng(z)]
                        if ys and any(y == x for y in ys): s += (2 if abs(i - j) == 1 else 1) / len(ys)
                return s
            first = cs[0]; tagfirst = t[3] in 'MN' and len(cs) > 1 and False
            t[2] = sorted(cs, key=lambda c: (-agree(c), cs.index(c) if t[4] else 0, pref(c)))[0]
# ---------------- 4. ids, labels, write ----------------
cnt = collections.Counter(t[1] for vs in chap.values() for v in vs for t in v[1] if t[1])
ids = {lem: i + 1 for i, (lem, n) in enumerate(sorted(cnt.items(), key=lambda x: (-x[1], x[0])))}
POSN = {'N': 'noun', 'A': 'adjective', 'RA': 'article', 'RP': 'pronoun', 'RR': 'relative pronoun', 'RD': 'demonstrative pronoun', 'RI': 'pronoun',
        'V': 'verb', 'P': 'preposition', 'C': 'conjunction', 'D': 'adverb', 'X': 'particle', 'I': 'interjection', 'M': 'numeral'}
TN = {'P': 'present', 'I': 'imperfect', 'F': 'future', 'A': 'aorist', 'X': 'perfect', 'Y': 'pluperfect'}
VN = {'A': 'active', 'M': 'middle', 'P': 'passive', 'E': 'middle/passive'}
MN = {'I': 'indicative', 'S': 'subjunctive', 'O': 'optative', 'D': 'imperative', 'N': 'infinitive', 'P': 'participle'}
CN = {'N': 'nominative', 'G': 'genitive', 'D': 'dative', 'A': 'accusative', 'V': 'vocative'}; NN = {'S': 'singular', 'P': 'plural', 'D': 'dual'}; GN = {'M': 'masculine', 'F': 'feminine', 'N': 'neuter'}
def label(c):
    p = c.split('.')[0]; r = c.split('.')[1] if '.' in c else ''
    if p == 'V' and r:
        m = re.match(r'([PIFAXY])([AMPE])([ISODNP])(.*)', r); s = f'{TN[m.group(1)]} {VN[m.group(2)]} {MN[m.group(3)]}'; rest = m.group(4)
        if m.group(3) == 'P' and len(rest) == 3: s += f', {CN[rest[0]]} {NN[rest[1]]} {GN[rest[2]]}'
        elif len(rest) == 2: s += f', {rest[0]}{"st" if rest[0]=="1" else "nd" if rest[0]=="2" else "rd"} person {NN[rest[1]]}'
        elif len(rest) == 1: s += f', {NN[rest[0]]}'
        return 'verb: ' + s
    if r:
        parts = [CN.get(r[0], ''), NN.get(r[1:2], '') if len(r) > 1 else '', GN.get(r[2:3], '') if len(r) > 2 else '']
        return POSN.get(p, 'noun') + ': ' + ' '.join(x for x in parts if x)
    return POSN.get(p, 'word')
mcodes, midx = [], {}
def mi(c):
    if c not in midx: midx[c] = len(mcodes); mcodes.append([c, label(c) if c else ''])
    return midx[c]
mi('')
for name in os.listdir(D):
    if name[0].isupper() or name[0].isdigit(): shutil.rmtree(os.path.join(D, name))
for sub in ('bw', 'en2', 'wk', 'occ', 'forms', 'dict', 'lsj', 'etym'): shutil.rmtree(os.path.join(D, sub), ignore_errors=True)
books = []; wk = collections.defaultdict(dict); stat = collections.Counter()
for code, bid, name in ORDER:
    chs = sorted({c for (b, c) in chap if b == bid})
    if not chs: continue
    os.makedirs(f'{D}/{bid}', exist_ok=True)
    for c in chs:
        vs = []
        for v, toks, en in chap[(bid, c)]:
            row = []
            for i, (w, lem, mc, src, _) in enumerate(toks):
                if src == 'K':      # CC BY-SA link: kept out of the main file
                    wk[(bid, c)].setdefault(str(v), {})[i] = [ids[lem], mi(mc)]; row.append([w, 0, 0])
                else: row.append([w, ids[lem] if lem else 0, mi(mc) if lem else 0])
            vs.append([str(v), row, en])
        json.dump(vs, open(f'{D}/{bid}/{c}.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    books.append({'id': bid, 'name': name, 'chapters': chs, 'en': True})
for (b, c), d in wk.items():
    os.makedirs(f'{D}/wk/{b}', exist_ok=True); json.dump(d, open(f'{D}/wk/{b}/{c}.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
os.makedirs(f'{D}/wk', exist_ok=True); json.dump(sorted(f'{b}/{c}' for b, c in wk), open(f'{D}/wk/index.json', 'w'), separators=(',', ':'))
json.dump(books, open(f'{D}/books.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
json.dump(mcodes, open(f'{D}/morph.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
# lexicon: [lemma, gloss(filled by plainmeaning), pos, translit, beta, strong]
POSL = {'V': 'Verb', 'N': 'Noun', 'A': 'Adjective', 'ADV': 'Adverb', 'PREP': 'Preposition', 'CONJ': 'Conjunction', 'PRT': 'Particle', 'T': 'Article', 'P': 'Pronoun', 'R': 'Pronoun', 'D': 'Pronoun', 'I': 'Pronoun', 'INJ': 'Interjection', 'COND': 'Conjunction'}
TBX = json.load(open(W + '/tbesg.json')); lex = {}
TRN = {}
for l in open('/workspace/lxx-audit/src/tbesg.txt', encoding='utf-8'):
    r = l.rstrip('\n').split('\t')
    if len(r) > 5 and re.match(r'G\d', r[0]): TRN.setdefault(re.match(r'G\d+', r[0]).group(), r[4])
for lem, i in ids.items():
    hw = AN.headword(lem); st = hw[0] if hw else ''; tbp = hw[2] if hw else ''; tr = TBX.get(st, ['', '', ''])
    m = re.match(r'[GN]:([A-Z]+)(?:-([A-Z]))?(?:-([A-Z]))?', tbp or '')
    pos = (POSL.get(m.group(1), m.group(1)) if m else '') + (' (name)' if tbp.endswith('-P') or tbp.endswith('-L') or tbp.endswith('-T') else '')
    # transliteration from TBESG column 5 when the dictionary entry is TBESG
    trn = ''
    for l in AN.HW.get(norm(lem), []):
        if l[0] == st: break
    lex[i] = [lem, '', pos.strip(), TRN.get(st, ''), to_beta(lem), st]
json.dump(lex, open(f'{D}/lexicon.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
# occurrences + counts
occ = collections.defaultdict(list); cn = collections.Counter()
for code, bid, name in ORDER:
    for c in sorted({c for (b, c) in chap if b == bid}):
        for v, toks, en in chap[(bid, c)]:
            seen = set()
            for w, lem, mc, src, _ in toks:
                if not lem: continue
                k = ids[lem]; cn[k] += 1
                if k not in seen: seen.add(k); occ[k].append(f'{bid}|{c}|{v}')
os.makedirs(f'{D}/occ', exist_ok=True); bk = collections.defaultdict(dict)
for k, r in occ.items(): bk[k // 100][k] = [cn[k]] + r
for b, d in bk.items(): json.dump(d, open(f'{D}/occ/{b}.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
json.dump(cn, open(f'{D}/counts.json', 'w'), separators=(',', ':'))
for f in ('gloss_fixes.json', 'gloss_pick.json', 'parse_overrides.json', 'regloss_log.csv', 'chapnotes.json', 'notes.json'):
    if os.path.exists(f'{D}/{f}'): os.remove(f'{D}/{f}')
json.dump({}, open(f'{D}/chapnotes.json', 'w')); json.dump({}, open(f'{D}/notes.json', 'w'))
n = sum(TOKSRC.values())
rep = {'tokens': n, 'by_route': {k: [v, round(100 * v / n, 2)] for k, v in TOKSRC.most_common()}, 'lemmas': len(ids), 'morph_codes': len(mcodes), 'pairing': pair}
json.dump(rep, open(W + '/build_report.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps({k: rep[k] for k in ('tokens', 'by_route', 'lemmas', 'morph_codes')}))
# keep the token-level choice for the self-check sampler
json.dump({f'{b}|{c}': [[v, [[w, lem, mc, src] for w, lem, mc, src, _ in toks]] for v, toks, en in vs] for (b, c), vs in chap.items()}, open(W + '/tokens.json', 'w'), ensure_ascii=False)

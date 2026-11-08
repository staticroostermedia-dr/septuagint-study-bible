#!/usr/bin/env python3
"""Build the New Testament layer (Greek + dictionary forms + grammar + WEB English).
Greek words, dictionary forms, Strong's numbers and grammar: STEPBible TAGNT (CC BY 4.0), words marked as in NA28.
English: World English Bible (eBible.org eng-web, public domain).
Usage: build_nt.py TAGNT_DIR ENG_WEB_VPL_TXT SITE_DIR   (writes data/<NTbook>/*.json, updates books.json, lexicon.json, morph.json)"""
import json, os, re, sys, unicodedata, collections
TAG, WEB, SITE = sys.argv[1:4]
D = os.path.join(SITE, 'data')
NT = [('Mat','Matt','Matthew','MAT'),('Mrk','Mark','Mark','MAR'),('Luk','Luke','Luke','LUK'),('Jhn','John','John','JOH'),('Act','Acts','Acts','ACT'),
 ('Rom','Rom','Romans','ROM'),('1Co','1Cor','1 Corinthians','1CO'),('2Co','2Cor','2 Corinthians','2CO'),('Gal','Gal','Galatians','GAL'),('Eph','Eph','Ephesians','EPH'),
 ('Php','Phil','Philippians','PHI'),('Col','Col','Colossians','COL'),('1Th','1Thess','1 Thessalonians','1TH'),('2Th','2Thess','2 Thessalonians','2TH'),
 ('1Ti','1Tim','1 Timothy','1TI'),('2Ti','2Tim','2 Timothy','2TI'),('Tit','Titus','Titus','TIT'),('Phm','Phlm','Philemon','PHM'),('Heb','Heb','Hebrews','HEB'),
 ('Jas','Jas','James','JAM'),('1Pe','1Pet','1 Peter','1PE'),('2Pe','2Pet','2 Peter','2PE'),('1Jn','1John','1 John','1JO'),('2Jn','2John','2 John','2JO'),
 ('3Jn','3John','3 John','3JO'),('Jud','Jude','Jude','JUD'),('Rev','Rev','Revelation','REV')]
T2ID = {t: i for t, i, n, w in NT}
CASE = dict(N='nominative', G='genitive', D='dative', A='accusative', V='vocative')
NUM = dict(S='singular', P='plural'); GEN = dict(M='masculine', F='feminine', N='neuter')
TNS = dict(P='present', I='imperfect', F='future', A='aorist', X='perfect', Y='pluperfect')
VOI = dict(A='active', M='middle', P='passive', E='middle/passive', D='middle (deponent)', O='passive (deponent)', N='middle/passive (deponent)')
MOOD = dict(I='indicative', S='subjunctive', O='optative', D='imperative', N='infinitive', P='participle')
POSN = dict(N='noun', A='adjective', RA='article', RP='personal pronoun', RR='relative pronoun', RD='demonstrative pronoun', RI='interrogative/indefinite pronoun',
            C='conjunction', P='preposition', D='adverb', X='particle', I='interjection', F='foreign word (indeclinable)')
def cng(s):
    m = re.match(r'([NGDAV])([SP])([MFN])?', s); 
    return (m.group(0), ', '.join(x for x in [CASE[m.group(1)] + ' ' + NUM[m.group(2)] + (' ' + GEN[m.group(3)] if m.group(3) else '')])) if m else ('', '')
def conv(r):
    """Robinson-style TAGNT code -> (site code, description). Unknown -> ('', '')."""
    r = re.sub(r'-(P|L|T|G|C|S|ATT|ABB|K|I|N|LI|PG|OI)$', '', r) if not r.startswith(('V-', 'S-')) else r
    p = r.split('-')
    h = p[0]
    simple = {'CONJ': 'C', 'COND': 'C', 'PREP': 'P', 'ADV': 'D', 'PRT': 'X', 'INJ': 'I', 'HEB': 'F', 'ARAM': 'F'}
    if h in simple: c = simple[h]; return c, POSN[c]
    if h == 'V':
        m = re.match(r'2?([PIFARL])([AMPEDON])([ISODNPM])', p[1]) if len(p) > 1 else None
        if not m: return '', ''
        t = {'R': 'X', 'L': 'Y'}.get(m.group(1), m.group(1)); v, md = m.group(2), {'M': 'D'}.get(m.group(3), m.group(3))
        rest = p[2] if len(p) > 2 else ''
        code = 'V.' + t + v + md; d = 'verb: ' + TNS[t] + ' ' + VOI[v] + ' ' + MOOD[md]
        if md == 'P':
            cc, dd = cng(rest)
            if cc: code += cc; d += ', ' + dd
        elif md != 'N':
            mm = re.match(r'([123])([SP])', rest)
            if mm: code += mm.group(0); d += ', ' + {'1': '1st', '2': '2nd', '3': '3rd'}[mm.group(1)] + ' person ' + NUM[mm.group(2)]
        return code, d
    pmap = {'N': 'N', 'A': 'A', 'T': 'RA', 'P': 'RP', 'F': 'RP', 'C': 'RP', 'R': 'RR', 'D': 'RD', 'I': 'RI', 'X': 'RI', 'Q': 'RI', 'K': 'RR', 'S': 'A'}
    if h not in pmap or len(p) < 2: return '', ''
    pos = pmap[h]; body = p[1]
    if h in 'PFS': body = re.sub(r'^[123]', '', body)
    if h == 'S': body = re.sub(r'^[SP]', '', body)
    if h == 'A' and re.match(r'^NUI$', body): return 'A', 'adjective (number, indeclinable)'
    if h == 'N' and body in ('PRI', 'LI', 'OI'): return 'N', 'noun (indeclinable)'
    cc, dd = cng(body)
    if not cc: return pos, POSN[pos]
    return pos + '.' + cc, POSN[pos] + ': ' + dd
def nrm(s): return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn').lower().replace('ς', 'σ')
PUN = re.compile('[\u037e\\[\\]().,;:\u00b7\u0387\u2e00-\u2e05\u2014\u2013\u201c\u201d"\u00ab\u00bb\u00b6]')
lex = json.load(open(os.path.join(D, 'lexicon.json'))); morph = json.load(open(os.path.join(D, 'morph.json')))
mi = {m[0]: i for i, m in enumerate(morph)}
bystrong = collections.defaultdict(list)
for k, v in lex.items(): bystrong[v[5]].append(k)
nextid = max(int(k) for k in lex) + 1; FIRSTNEW = nextid; newlex = 0
def STEM(x): return re.sub('(ομαι|υμι|μι|ω|ον|οσ)$', '', nrm(x))
def lexid(strong, lemma, gloss, pos):
    global nextid, newlex
    base = re.match(r'G\d+', strong).group(0) if re.match(r'G\d+', strong) else strong
    base = 'G%04d' % int(base[1:]) if base[1:].isdigit() else base
    cands = bystrong.get(base, [])
    for k in cands:
        if nrm(lex[k][0]) == nrm(lemma): return k
    for k in cands:   # same Strong's number and a spelling variant of the same word (e.g. ἀπολλύω / ἀπόλλυμι); otherwise keep TAGNT's own form
        if STEM(lex[k][0]) == STEM(lemma): return k
    k = str(nextid); nextid += 1; newlex += 1
    lex[k] = [lemma, gloss, pos, '', '', base, 'T', [[gloss, 'T']]]; bystrong[base].insert(0, k); return k
NOM = collections.Counter(); words = collections.OrderedDict(); stats = collections.Counter()
for fn in ('mj.txt', 'ar.txt'):
    for line in open(os.path.join(TAG, fn), encoding='utf-8'):
        f = line.rstrip('\n').split('\t')
        m = re.match(r'^([1-3A-Z][A-Za-z]{2})\.(\d+)\.(\d+)(?:[\(\[\{][^\)\]\}]*[\)\]\}])?#(\d+)=([\w()]+)$', f[0])
        if not m or len(f) < 6: continue
        if 'NA28' not in f[5]: stats['skipped_not_NA28'] += 1; continue
        b, c, v = T2ID[m.group(1)], m.group(2), m.group(3)
        form = unicodedata.normalize('NFC', PUN.sub('', f[1].split(' (')[0]).strip())
        if not form: continue
        st, code = (f[3].split('=', 1) + [''])[:2]
        lemma, gloss = (f[4].split('=', 1) + [''])[:2]
        lemma = lemma.split(',')[0].strip()   # 'ὅς, ἥ' -> 'ὅς'
        crasis = ' + ' in code
        sc, desc = conv(code.split('=')[-1] if crasis else code)
        if crasis: stats['crasis_words_tagged_by_last_part'] += 1
        if sc and sc not in mi: mi[sc] = len(morph); morph.append([sc, desc])
        if not sc: stats['no_morph'] += 1; NOM[code] += 1
        pos = POSN.get(sc.split('.')[0], '').split(' ')[0].capitalize() if sc else ''
        lid = int(lexid(st, lemma, gloss.split('/')[0] if gloss else '', pos)) if lemma else 0
        if not lid: stats['no_lemma'] += 1
        words.setdefault((b, int(c)), collections.OrderedDict()).setdefault(int(v), []).append([form, lid, mi.get(sc, 0)])
        stats['words'] += 1
web = collections.defaultdict(dict); W2ID = {w: i for t, i, n, w in NT}
for line in open(WEB, encoding='utf-8'):
    m = re.match(r'^(\w+) (\d+):(\d+) (.*)$', line.strip())
    if m and m.group(1) in W2ID: web[(W2ID[m.group(1)], int(m.group(2)))][int(m.group(3))] = m.group(4).strip()
books = [b for b in json.load(open(os.path.join(D, 'books.json'))) if not b.get('nt')]
for t, i, n, w in NT:
    chs = sorted(set(c for (b, c) in words if b == i) | set(c for (b, c) in web if b == i))
    os.makedirs(os.path.join(D, i), exist_ok=True)
    for c in chs:
        g = words.get((i, c), {}); e = web.get((i, c), {})
        out = []
        for v in sorted(set(g) | set(e)):
            row = [str(v), g.get(v, []), e.get(v, '')]
            if v not in g: row.append({'s': 'g0'}); stats['verses_english_only'] += 1
            if v not in e: stats['verses_greek_only'] += 1
            out.append(row)
        json.dump(out, open(os.path.join(D, i, '%d.json' % c), 'w'), ensure_ascii=False, separators=(',', ':'))
    books.append({'id': i, 'name': n, 'chapters': chs, 'en': True, 'nt': True})
json.dump(books, open(os.path.join(D, 'books.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
json.dump(lex, open(os.path.join(D, 'lexicon.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
json.dump(morph, open(os.path.join(D, 'morph.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
stats['new_lexicon_entries'] = newlex
# Abbott-Smith (STEPBible TBESG, CC BY 4.0) entries for the new NT dictionary forms, in the same bucket format as data/dict/
TB = sys.argv[4] if len(sys.argv) > 4 else None
if TB:
    tb = {}
    for line in open(TB, encoding='utf-8'):
        f = line.rstrip('\n').split('\t')
        if len(f) > 7 and re.match(r'^G\d{4}', f[0]) and f[0] == f[2]: tb.setdefault(f[0], f)
    buckets = {}; added = 0
    for k in range(FIRSTNEW, nextid):
        k = str(k); L = lex[k]; e = tb.get(L[5])
        if not e: continue
        bk = int(k) // 100
        if bk not in buckets:
            fp = os.path.join(D, 'dict', '%d.json' % bk); buckets[bk] = json.load(open(fp)) if os.path.exists(fp) else {}
        full = e[7].strip(); bs = [re.sub('<[^>]+>', '', x).strip(' ,;:') for x in re.findall(r'<b>(.*?)</b>', full)[1:]]
        bs = [x for x in bs if x and not re.search('[\u0370-\u03ff\u1f00-\u1fff]', x)][:8]
        buckets[bk][k] = {'id': L[5], 'g': e[6], 's': bs or [e[6]], 'lxx': '', 'full': full}; added += 1
    os.makedirs(os.path.join(D, 'dict'), exist_ok=True)
    for bk, d in buckets.items(): json.dump(d, open(os.path.join(D, 'dict', '%d.json' % bk), 'w'), ensure_ascii=False, separators=(',', ':'))
    stats['new_entries_with_abbott_smith'] = added
print(json.dumps(stats, indent=1)); print(NOM.most_common(15))

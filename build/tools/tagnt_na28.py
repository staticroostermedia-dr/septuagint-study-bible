"""TAGNT (STEPBible, CC BY 4.0) -> the NA28 words, in order, one per TAGNT row. Shared by build_nt.py, check_nt_lemmas.py, ntrefs.py,
na28_variant_tokens.py and the NT-wide token test.

TAGNT's main columns give one edition set per row (column 6, e.g. 'NA28+NA27+Tyn+WH+TR+Byz'). Where NA28 reads differently from the word in
the main columns, the main word is the TR/Byz (or NA27...) reading and the NA28 word is ONLY in the variant column (column 7), as
'κατέγραφεν (o=kategraphen) he was delineating - G6047=V-IAI-3S in: NA28+NA27+Tyn+WH', several entries separated by ' ¦ '.
Before 2026-11-27 build_nt.py dropped those rows (64 NA28 words in 59 verses, e.g. John 8:6 κατέγραφεν, 8:10 Γύναι, Jude 1:5 Ἰησοῦς).
row() now returns the NA28 word from the variant column, with its own Strong's number, grammar code and gloss; the dictionary form
(not given in the variant column) comes from TAGNT's own lemma for that Strong's number elsewhere, else the TBESG headword."""
import os, re, unicodedata, collections
REF = re.compile(r'^([1-3A-Z][A-Za-z]{2})\.(\d+)\.(\d+)(?:[\(\[\{][^\)\]\}]*[\)\]\}])?#(\d+)=([\w()]+)$')
VAR = re.compile(r'^(?P<form>\S+) \([^)]*\) ?(?P<gloss>.*?) - (?P<strong>G\d+[A-Za-z]?)=(?P<code>\S+) in: (?P<eds>[\w+«»]+)\s*$')
PUN = re.compile('[\u037e\\[\\]().,;:\u00b7\u0387\u2e00-\u2e05\u2014\u2013\u201c\u201d"\u00ab\u00bb\u00b6]')
TAG = '/workspace/src/tagnt'
def eds(s): return [re.split('[«»]', e)[0] for e in s.split('+')]   # 'NA28»2' (word order mark) -> 'NA28'
def lines(tag=TAG):
    for fn in ('mj.txt', 'ar.txt'):
        for line in open(os.path.join(tag, fn), encoding='utf-8'):
            f = line.rstrip('\n').split('\t'); m = REF.match(f[0])
            if m and len(f) >= 6: yield m, f
_LEM = {}
def lemmas(tag=TAG, tbesg=None):
    """Strong's number (as written, and the bare G#### base) -> TAGNT dictionary form 'lemma=gloss' from the main columns."""
    if tag in _LEM: return _LEM[tag]
    d = {}
    for m, f in lines(tag):
        st = f[3].split('=', 1)[0]
        for k in (st, re.match(r'G\d+', st).group(0) if re.match(r'G\d+', st) else st): d.setdefault(k, f[4])
    if tbesg and os.path.exists(tbesg):
        for line in open(tbesg, encoding='utf-8'):
            x = line.rstrip('\n').split('\t')
            if len(x) > 6 and re.match(r'^G\d{4}', x[0]) and x[0] == x[2]: d.setdefault(x[0], x[3] + '=' + x[6])
    _LEM[tag] = d; return d
# Greek Maestro's corrections to TAGNT variant-column entries: (book, ch, v, TAGNT form) -> (NA28 form, lemma, gloss)
FIX = {('Act', 18, 7, 'Τιτου'): ('Τιτίου', 'Τίτιος', 'Titius')}   # NA28 Τιτίου Ἰούστου, 'Titius Justus' (G6084); not Τίτος 'Titus' (2026-11-27)
def row(m, f, tag=TAG, tbesg='/workspace/lxx-audit/src/tbesg.txt'):
    r = _row(m, f, tag, tbesg)
    if r and r[5] == 'variant':
        x = FIX.get((m.group(1), int(m.group(2)), int(m.group(3)), r[0]))
        if x: r = (x[0], r[1], r[2], x[1], x[2], 'variant')
    return r
def _row(m, f, tag=TAG, tbesg='/workspace/lxx-audit/src/tbesg.txt'):
    """(form, strong, code, lemma, gloss, how) for an NA28 word, how = 'main' | 'variant'; None if NA28 has no word here."""
    if 'NA28' in eds(f[5]):
        st, code = (f[3].split('=', 1) + [''])[:2]; lemma, gloss = (f[4].split('=', 1) + [''])[:2]
        return f[1].split(' (')[0], st, code, lemma, gloss, 'main'
    if len(f) < 7 or 'NA28' not in f[6]: return None
    for alt in f[6].split('¦'):
        v = VAR.match(alt.strip())
        if v and 'NA28' in eds(v.group('eds')):
            st = v.group('strong'); L = lemmas(tag, tbesg)
            lg = L.get(st) or L.get(re.match(r'G\d+', st).group(0) + ('' if st[-1].isdigit() else '')) or L.get('G%04d' % int(re.match(r'G(\d+)', st).group(1)))
            lemma, gloss = ((lg or '=').split('=', 1) + [''])[:2]
            return v.group('form'), st, v.group('code'), lemma, gloss or v.group('gloss'), 'variant'
    return None
def form(w): return unicodedata.normalize('NFC', PUN.sub('', w).strip())
def na28_words(tag=TAG):
    """{(TAGNT book, ch, v): [(form, strong, code, lemma, gloss, how), ...]} in TAGNT order; empty forms dropped (as in build_nt.py)."""
    out = collections.OrderedDict()
    for m, f in lines(tag):
        r = row(m, f, tag)
        if r and form(r[0]): out.setdefault((m.group(1), int(m.group(2)), int(m.group(3))), []).append((form(r[0]),) + r[1:])
    return out

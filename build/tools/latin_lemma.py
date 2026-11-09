"""Latin lemma + confidence for one Vulgate word (LatinCy output + Whitaker's Words check + Lewis & Short headword).
A lemma/meaning is SHOWN only when all checks pass; otherwise the app hides it (never shows a guess)."""
import re, json, os, unicodedata
from latin_whitaker import agree, analyse_enc
HERE = os.path.dirname(os.path.abspath(__file__))
T_SCORE = float(os.environ.get('LAT_T', '0.80'))   # LatinCy edit-tree lemmatizer probability needed to show a lemma
def n(s): s = ''.join(c for c in unicodedata.normalize('NFD', s) if not unicodedata.combining(c)); return s.lower().replace('æ', 'ae').replace('œ', 'oe').replace('v', 'u').replace('j', 'i')
# Known LatinCy errors in the Vulgate (data-stage review): fixed here.
def fix(form, lemma, pos):
    f = n(form)
    if f in ('salutare', 'salutari') and n(lemma) in ('saluto', 'salutaris') and pos in ('NOUN', 'VERB'): return 'salutare', 'NOUN'
    if form == 'Do' and pos == 'PROPN': return 'do', 'VERB'
    if n(lemma) == 'eo' and pos in ('PRON', 'DET'): return 'is', 'PRON'
    if pos == 'PROPN' and n(lemma) == f and any(a[0] == 'V' for a in analyse_enc(f)) and not any(a[0] == 'N' for a in analyse_enc(f)): return lemma, 'X'   # capitalised common verb read as a name: hide
    return lemma, pos
# Lewis & Short spells some Vulgate headwords differently.
LS_ALIAS = {'altare': 'altaria', 'coepi': 'coepio', 'reuertor': 'reuerto', 'salutare': 'salutaris', 'obedio': 'oboedio', 'brachium': 'bracchium',
            'caeremonia': 'caerimonia', 'solemnitas': 'sollemnitas', 'adnuntio': 'annuntio', 'haeredito': 'hereditas', 'extinguo': 'exstinguo',
            'uidua': 'uiduus', 'excelsum': 'excelsus', 'absconditus': 'abscondo', 'benedictus': 'benedico', 'semetipse': 'ipse', 'idolon': 'idolum',
            'reliquia': 'reliquiae', 'primitia': 'primitiae', 'retrorsus': 'retrorsum', 'resisto': 'resisto', 'haereditas': 'hereditas', 'haeres': 'heres'}
def ls_variants(l):
    yield l
    if l in LS_ALIAS: yield LS_ALIAS[l]
    for a, b in (('ae', 'e'), ('e', 'ae'), ('oe', 'e'), ('adn', 'ann'), ('adt', 'att'), ('adp', 'app'), ('adc', 'acc'), ('ads', 'ass'), ('inm', 'imm'), ('inp', 'imp'), ('conl', 'coll'), ('conr', 'corr'), ('exs', 'ex'), ('ex', 'exs'), ('h', ''), ('mn', 'm'), ('ch', 'cch'), ('ii', 'i')):
        if a in l: yield l.replace(a, b, 1)
    if l.endswith('a'): yield l[:-1] + 'us'
    if l.endswith('or'): yield l[:-2] + 'o'
def ls_key(l, LS):
    for v in ls_variants(n(l)):
        if v in LS and any(e['g'] for e in LS[v]): return v
    return ''
def judge(form, lemma, pos, score, LS):
    """-> (lemma, pos, lskey, show) ; show: 2 = lemma + meaning, 1 = name (no meaning), 0 = hide"""
    lemma, pos = fix(form, lemma, pos)
    if pos in ('X', 'PUNCT', '') or not lemma: return lemma, pos, '', 0
    fixed = (n(form) in ('salutare', 'salutari', 'do', 'eo'))
    if score < T_SCORE and not fixed: return lemma, pos, '', 0
    a = agree(form, lemma, pos)
    if pos == 'PROPN': return lemma, pos, '', (1 if a is None else 0)
    if a is not True and not fixed: return lemma, pos, '', 0
    k = ls_key(lemma, LS)
    return lemma, pos, k, (2 if k else 0)

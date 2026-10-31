"""Shared helpers: tokenizing Brenton Greek, Unicode<->Beta Code, normalisation."""
import re, unicodedata as u
GRC = '/workspace/lxx-audit/src/grcbrent/grcbrent_vpl.txt'
ENG = '/workspace/brenton/eng-Brenton_vpl.txt'
def vpl(p):
    d = {}
    for l in open(p, encoding='utf-8-sig'):
        m = re.match(r'(\S+) (\d+):(\d+[a-z]*) (.*)', l.rstrip('\n'))
        if m: d[(m.group(1), int(m.group(2)), m.group(3))] = m.group(4).strip()   # verse kept as text: lettered verses such as 31:50a
    return d
PUNCT = ',.·;:!?“”‘’()[]«»—\u0387\u037e'
def tokens(text):
    out = []
    for w in text.split():
        w = w.strip(PUNCT).lstrip('ʼ\u2019\'')
        w = u.normalize('NFC', w.replace('\u0323', ''))
        if w: out.append(w)
    return out
def acute(s): return u.normalize('NFC', u.normalize('NFD', s).replace('\u0300', '\u0301'))
def lower_form(s):
    """Brenton prints the first word of a book/chapter in capitals (ἘΝ, ΜΑΚΑΡΙΟΣ) and capitalises Θεὸς/Κύριος."""
    return acute(s).lower()
def norm(s):
    s = ''.join(c for c in u.normalize('NFD', s) if not u.combining(c)).lower().replace('ς', 'σ')
    return u.normalize('NFC', re.sub(r'[^\w]', '', s))
B = dict(zip('αβγδεζηθικλμνξοπρστυφχψωςϲ', 'abgdezhqiklmncoprstufxywss'))
DIA = {'\u0313': ')', '\u0314': '(', '\u0301': '/', '\u0300': '\\', '\u0342': '=', '\u0308': '+', '\u0345': '|'}
def to_beta(w):
    out = ''
    for ch in u.normalize('NFD', w.lower()):
        if ch in B: out += B[ch]
        elif ch in DIA: out += DIA[ch]
        elif ch in 'ʼ\u2019\'': out += "'"
        elif u.combining(ch): pass
        else: out += ch
    return out
RB = {v: k for k, v in B.items() if k not in 'ςϲ'}
RDIA = {v: k for k, v in DIA.items()}
def from_beta(b):
    b = re.sub(r'\d+$', '', b.strip())
    out, cap, pend = '', False, ''
    for ch in b:
        if ch == '*': cap = True; continue
        if ch in RB:
            out += (RB[ch].upper() if cap else RB[ch]) + pend; cap = False; pend = ''
        elif ch in RDIA:
            if cap: pend += RDIA[ch]
            else: out += RDIA[ch]
        elif ch == '-': continue
        else: out += ch
    out = re.sub(r'σ(?=$|[^\w\u0300-\u036f])', 'ς', u.normalize('NFC', out))
    # capital words in beta put diacritics before the letter: handled loosely
    return u.normalize('NFC', out)
def to_beta_cap(w):
    """Capitalised word -> Beta Code '*)abraa/m' (diacritics of the capital go after the asterisk)."""
    b = to_beta(w)
    m = re.match(r"([a-z])([()/\\=+|]*)(.*)", b)
    return '*' + m.group(2) + m.group(1) + m.group(3) if m else b
def is_cap(w): return w[:1].isupper() and not w[1:2].isupper()

def vkey(v):
    m = re.match(r'(\d+)([a-z]*)', str(v)); return (int(m.group(1)), m.group(2))

"""Etymology cleanup (Gallicantus batch): Wiktionary etymology_text often starts with an 'Etymology tree' block (one ancestor per line, e.g.
'Proto-Indo-European *dʰeh₁-' ... 'Ancient Greek θεός'). enrich.py flattened those lines into the sentence, giving garbled text such as
'Etymology tree Proto-Indo-European *dʰeh₁- Proto-Indo-European *-s …'. This rewrites only the affected entries of data/etym/ from the local kaikki dump
(/workspace/src/grc_kaikki.jsonl, the same file enrich.py read): the tree lines are dropped and the prose that follows is shortened as before.
An entry whose etymology is only a tree (no prose) is removed (no Etym. row rather than a garbled one). Usage: python3 build/tools/etym_clean.py"""
import json, os, re, sys, unicodedata
sys.path.insert(0, os.path.dirname(__file__))
D = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
SRC = '/workspace/src/grc_kaikki.jsonl'
def nw(s): return unicodedata.normalize('NFC', ''.join(c for c in unicodedata.normalize('NFD', s) if c not in '\u0304\u0306'))
def gk(t):
    t = unicodedata.normalize('NFD', t)
    t = re.sub(r'(?<=[\u0370-\u03ff\u1f00-\u1fff])([\u0300-\u036f]*)[\u0304\u0306]', r'\1', t)
    t = re.sub(r'([\u0370-\u03ff][\u0300-\u036f]*)[\u0304\u0306]', r'\1', t)
    return unicodedata.normalize('NFC', t)
def short(t):
    t = re.sub(r'\s+', ' ', t).strip()
    sents = re.split(r'(?<=\.)\s+(?=[A-Z])', t)
    out = sents[0]
    if len(sents) > 1 and len(out) + len(sents[1]) < 230: out += ' ' + sents[1]
    return out if len(out) <= 260 else out[:257].rsplit(' ', 1)[0] + '…'
TREE_LINE = re.compile(r'^(?:[A-Z][\w-]*(?: [A-Z][\w-]*)*|Ancient Greek|Proto-Indo-European|Proto-Hellenic)(?: [\w-]+)? ?(\S+)?(?: \([^()]*\))?\??$')
def is_tree_line(s):
    """an ancestor line: a language name, then one term (often starred), optionally a transliteration in brackets; no sentence words"""
    s = s.strip()
    if not s or s == '▲': return True
    s = re.sub(r'(?<=\S)(der|influ|inh|bor|lbor|slbor|ubor|obor|calq|clq|sl|af|lg|psm|translit|ono|abbrev)\.?$', '', s)
    s0 = s; s = re.sub(r'(?:^| )[*-]\S*', ' ', s)
    if re.search(r'\b(from|of|with|and|the|is|see|cognate|related|whence|compare|probably|perhaps|uncertain)\b', s): return False
    if '“' in s0 or s0.endswith(('.', ':', ';')) and not re.search(r'\*\S*\.$', s0): return False
    return len(s0.split()) <= 7
def strip_tree(t, head=None):
    """the tree ends with the entry's own line 'Ancient Greek <headword>': cut there when it is found"""
    if head and t.startswith(('Etymology tree', 'PIE word')):
        ls = t.split('\n')
        for i, ln in enumerate(ls):
            if nw(ln.strip()) == 'Ancient Greek ' + nw(head): return '\n'.join(ls[i + 1:]).strip()
    return strip_lines(t)
def strip_lines(t):
    """drop leading tree material: 'PIE word' / 'Etymology tree' headings and ancestor lines, up to the first line of prose"""
    lines = t.split('\n'); out = []; lead = True
    for ln in lines:
        s = ln.strip()
        if lead and (re.match(r'^(PIE word|Etymology tree)\b', s) or ('Etymology tree' in t and is_tree_line(s)) or (len(lines) > 1 and TREE_START.match(s) and is_tree_line(s))): continue
        lead = False; out.append(ln)
    return '\n'.join(out).strip()
TREE_START = re.compile(r'^(Proto-[\w-]+|Ancient Greek|Mycenaean Greek|Latin|Old Latin) \S')
def clean(raw, head=None): t = strip_tree(raw, head); return gk(short(t)) if t else ''
if __name__ == '__main__':
    have = {}
    for f in os.listdir(D + '/etym'):
        d = json.load(open(f'{D}/etym/{f}', encoding='utf-8'))
        for k, v in d.items(): have[k] = f
    lex = json.load(open(D + '/lexicon.json', encoding='utf-8'))
    want = {nw(lex[k][0]): k for k in have}
    raw = {}
    for line in open(SRC, encoding='utf-8'):
        if '"etymology_text"' not in line: continue
        d = json.loads(line); w = nw(d.get('word', ''))
        if w in want and want[w] not in raw and d.get('etymology_text'): raw[want[w]] = d['etymology_text']
    bad = {k: have[k] for k, r in raw.items() if strip_tree(r, lex[k][0]) != r.strip()}
    fixed = dropped = 0; files = {}
    for k, f in bad.items():
        files.setdefault(f, json.load(open(f'{D}/etym/{f}', encoding='utf-8')))
        t = clean(raw.get(k, ''), lex[k][0])
        if t: files[f][k]['t'] = t; fixed += 1
        else: del files[f][k]; dropped += 1
    for f, d in files.items(): json.dump(d, open(f'{D}/etym/{f}', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(json.dumps({'tree_entries': len(bad), 'rewritten': fixed, 'removed_tree_only': dropped}))

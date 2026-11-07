#!/usr/bin/env python3
"""Pick the verses where LXX2012 differs MEANINGFULLY from the Brenton English shown, for a small 'LXX2012: ...' line in the word pop-up.
Idempotent; run in site/. Writes data/lx/<Book>/<ch>.json = {verse: [lxx2012 text, [[start, end], ...] spans of differing words]} and prints counts.
'Meaningful' = after normalising both texts, at least one content word is added, removed or replaced. Normalising ignores:
 case, punctuation, brackets, hyphens/spaces in compounds (alms-deeds/alms deeds); archaic forms (thee/thou/ye -> you, thy/thine -> your,
 mine -> my, hath -> has, doth -> does, -eth/-est verb endings, yea -> yes, art -> are, wilt/shalt/hast/dost -> will/shall/have/do);
 spelling and inflection variants (a replaced word at least 75% similar: Rasin/Rasim, way/ways); added/removed function words only (the, a, of, and ...).
Verses are skipped (not compared) when the two do not cover the same text: Brenton verse empty, or word overlap < 50%, or length ratio outside 0.6-1.67
(the two editions sometimes number or divide verses differently, e.g. Gen 3:1)."""
import json, os, re, difflib, shutil, collections, unicodedata
D = 'data'
ARCH = {'thee': 'you', 'thou': 'you', 'ye': 'you', 'thy': 'your', 'thine': 'your', 'mine': 'my', 'hath': 'has', 'doth': 'does', 'yea': 'yes',
        'art': 'are', 'wilt': 'will', 'shalt': 'shall', 'hast': 'have', 'dost': 'do', 'didst': 'did', 'wast': 'were', 'saith': 'says', 'unto': 'to',
        'yourselves': 'yourselves', 'thyself': 'yourself', 'canst': 'can', 'couldest': 'could', 'shouldest': 'should', 'wouldest': 'would', 'hadst': 'had', 'spake': 'spoke', 'brethren': 'brothers'}
FUNC = set('has have had do does did will shall would should can could may might the a an of and to in on at for by with from that which who whom this these those is are was were be been it its as or but so then there their them they he his him she her i me my we us our you your not no all also even being such o oh'.split())
def toks(s):
    s = ''.join(ch for ch in unicodedata.normalize('NFD', s) if unicodedata.category(ch) != 'Mn')
    s = s.replace('æ', 'ae').replace('Æ', 'Ae').replace('œ', 'oe').replace('\u2019', "'").replace('\u2018', "'")
    s = re.sub(r"\b[Cc]an't\b", 'cannot', s); s = re.sub(r"\b[Ww]on't\b", 'will not', s); s = re.sub(r"n't\b", ' not', s)
    s = re.sub(r"\bcan not\b", 'cannot', s)
    out = []
    for m in re.finditer(r"[A-Za-z']+", s.replace('-', ' ')):
        w = m.group(0).lower().strip("'")
        if not w: continue
        w = ARCH.get(w, w)
        if len(w) > 5 and w.endswith('eth'): w = w[:-3] + 's'
        elif len(w) > 5 and w.endswith('est') and w not in ('rest', 'best', 'west', 'priest', 'forest', 'harvest', 'interest', 'greatest'): w = w[:-3]
        out.append((w, m.start(), m.end()))
    return out
def STM(w): return re.sub('(ed|t|d|s)$', '', w)
def sim(a, b): return difflib.SequenceMatcher(None, a, b).ratio()
SYS_MIN = 5   # a one-word (or one-phrase) substitution made at least this many times across the OT is a systematic modernisation, not a different rendering
def pairs_of(a, bb):
    sm = difflib.SequenceMatcher(None, a, bb, autojunk=False)
    return sm, [(' '.join(a[i1:i2]), ' '.join(bb[j1:j2])) for op, i1, i2, j1, j2 in sm.get_opcodes() if op == 'replace' and i2 - i1 <= 2 and j2 - j1 <= 2]
def verses():
    for b in json.load(open(os.path.join(D, 'books.json'))):
        if b.get('nt'): continue
        for c in b['chapters']:
            p = os.path.join(D, 'en2', b['id'], '%s.json' % c)
            if not os.path.exists(p): continue
            yield b, c, json.load(open(os.path.join(D, b['id'], '%s.json' % c))), json.load(open(p))
PC = collections.Counter()
for b, c, vs, e2 in verses():
    for v in vs:
        if v[2] and e2.get(v[0]):
            a, bb = [x[0] for x in toks(v[2])], [x[0] for x in toks(e2[v[0]])]
            if a and bb and 0.6 <= len(bb) / len(a) <= 1.67: PC.update(pairs_of(a, bb)[1])
SYSTEMATIC = {k for k, n in PC.items() if n >= SYS_MIN}
shutil.rmtree(os.path.join(D, 'lx'), ignore_errors=True)
st = collections.Counter(); ex = []
for b, c, VS, e2 in verses():
    if True:
        out = {}
        for v in VS:
            br, lx = v[2] or '', e2.get(v[0], '')
            if not lx: st['no_lxx2012'] += 1; continue
            if not br: st['skipped_no_brenton'] += 1; continue
            if len(v) > 3 and v[3] and v[3].get('s') in ('r', 'm', 'j', 'h'): st['skipped_brenton_reseg'] += 1; continue   # Brenton's English was moved/matched across verses here
            st['compared_or_skipped'] += 1
            A, B = toks(br), toks(lx); a, bb = [x[0] for x in A], [x[0] for x in B]
            if not a or not bb or not (0.6 <= len(bb) / len(a) <= 1.67): st['skipped_alignment'] += 1; continue
            sm = difflib.SequenceMatcher(None, a, bb, autojunk=False)
            if sum(x.size for x in sm.get_matching_blocks()) / max(len(a), len(bb)) < 0.5: st['skipped_alignment'] += 1; continue
            st['compared'] += 1; spans = []
            for op, i1, i2, j1, j2 in sm.get_opcodes():
                if op == 'equal': continue
                x, y = a[i1:i2], bb[j1:j2]
                if all(w in FUNC for w in x + y): continue
                xc, yc = [w for w in x if w not in FUNC], [w for w in y if w not in FUNC]
                if len(xc) == len(yc) and all(sim(STM(p), STM(q)) >= 0.65 for p, q in zip(xc, yc)): continue
                if ''.join(x) == ''.join(y): continue   # compounds split/joined
                if op == 'replace' and (' '.join(x), ' '.join(y)) in SYSTEMATIC: continue
                if j2 > j1: spans.append([B[j1][1], B[j2 - 1][2]])
                elif i2 > i1: spans.append([-1, -1])     # LXX2012 leaves out Brenton words
            if spans:
                out[v[0]] = [lx, [s for s in spans if s[0] >= 0]]; st['meaningful'] += 1
                if len(ex) < 400: ex.append((b['id'], c, v[0], br, lx))
        if out:
            os.makedirs(os.path.join(D, 'lx', b['id']), exist_ok=True)
            json.dump(out, open(os.path.join(D, 'lx', b['id'], '%s.json' % c), 'w'), ensure_ascii=False, separators=(',', ':'))
json.dump(sorted(os.path.relpath(os.path.join(r, f), os.path.join(D, 'lx'))[:-5] for r, _, fs in os.walk(os.path.join(D, 'lx')) for f in fs), open(os.path.join(D, 'lx', 'index.json'), 'w'), separators=(',', ':'))
st['systematic_pairs_ignored'] = len(SYSTEMATIC)
print(json.dumps(st, indent=1)); print('top systematic:', sorted(((n, k) for k, n in PC.items() if k in SYSTEMATIC), reverse=True)[:40])
import random; random.seed(3)
for x in random.sample(ex, 8): print('\n%s %s:%s\n B: %s\n L: %s' % x)

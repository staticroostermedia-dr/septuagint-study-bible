#!/usr/bin/env python3
"""Headline gloss = the lemma's own licensed sense that best matches Brenton's usual wording (automatic).

Candidates come ONLY from the lemma's own entries: the LXX lexicon gloss parts (09a_LXX_lexicon, via lexicon.json),
Abbott-Smith (TBESG, data/dict) and LSJ (TFLSJ, data/lsj). Brenton's wording per lemma comes from data/bw (brentalign).
No definition is written by hand. Conservative: a gloss is changed only when Brenton's wording clearly supports another
sense and hardly ever matches the current one. Hand-reviewed glosses (gloss_fixes.json) are never touched.
Writes data/gloss_pick.json {lid: {old, new, src}} and updates lexicon.json L[1]; tools/gloss_review.tsv for review.
"""
import json, os, re, collections, sys
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'site'))
L = json.load(open('data/lexicon.json'))
if any(len(e) > 6 for e in L.values()): L = json.load(open(os.path.join('..', 'tools', '.lexicon_pre_plain.json')))  # after plainmeaning: use its saved input
CNT = json.load(open('data/counts.json'))
GFIX = json.load(open('data/gloss_fixes.json'))
PREV = json.load(open('data/gloss_pick.json')) if os.path.exists('data/gloss_pick.json') else {}
for k, p in PREV.items():                      # idempotent: restore the lexicon gloss before re-picking
    if k in L and L[k][1] == p['new']: L[k][1] = p['old']
POS = {'Noun', 'Verbs', 'Adjective', 'Adjective, Noun', 'Noun, Adjective'}
IRR = {}
for base, forms in {'go': 'went gone goeth goest', 'become': 'became', 'overcome': 'overcame', 'come': 'came', 'take': 'took taken', 'give': 'gave given', 'see': 'saw seen',
    'speak': 'spoke spake spoken', 'say': 'said saith', 'know': 'knew known', 'stand': 'stood', 'sit': 'sat', 'fall': 'fell fallen',
    'bring': 'brought', 'beget': 'begot begat begotten', 'bear': 'bore born borne', 'forsake': 'forsook forsaken', 'rise': 'rose arose risen arise',
    'write': 'wrote written', 'eat': 'ate eaten', 'slay': 'slew slain', 'break': 'broke broken', 'lead': 'led', 'keep': 'kept',
    'leave': 'left', 'seek': 'sought', 'find': 'found', 'tell': 'told', 'sell': 'sold', 'lay': 'laid', 'build': 'built builded',
    'overtake': 'overtook overtaken', 'smite': 'smote smitten', 'shake': 'shook shaken', 'choose': 'chose chosen', 'draw': 'drew drawn',
    'throw': 'threw thrown', 'hide': 'hid hidden', 'strike': 'struck stricken', 'fight': 'fought', 'catch': 'caught', 'teach': 'taught',
    'buy': 'bought', 'feel': 'felt', 'think': 'thought', 'dwell': 'dwelt', 'show': 'shew shewed shewn shewing shown', 'work': 'wrought',
    'run': 'ran', 'send': 'sent', 'mean': 'meant', 'hear': 'heard', 'make': 'made', 'do': 'did done doth', 'have': 'hath had has hast hadst',
    'be': 'is was were are am been', 'flee': 'fled', 'feed': 'fed', 'bind': 'bound', 'lift': 'lifted', 'fly': 'flew flown',
    'grow': 'grew grown', 'blow': 'blew blown', 'swear': 'swore sworn', 'tear': 'tore torn', 'wear': 'wore worn', 'begin': 'began begun',
    'drink': 'drank drunk', 'sing': 'sang sung', 'sink': 'sank sunk', 'spring': 'sprang sprung', 'forget': 'forgot forgotten',
    'hold': 'held', 'stay': 'staid', 'awake': 'awoke', 'lie': 'lay lain', 'sleep': 'slept', 'weep': 'wept', 'meet': 'met', 'win': 'won',
    'shine': 'shone', 'tread': 'trod trodden', 'ride': 'rode ridden', 'drive': 'drove driven', 'hang': 'hung', 'cleave': 'clave cleft',
    'abide': 'abode', 'forbid': 'forbade forbidden', 'shoot': 'shot', 'light': 'lit', 'stick': 'stuck', 'strive': 'strove striven',
    'wake': 'woke', 'deal': 'dealt', 'lend': 'lent', 'bend': 'bent', 'spend': 'spent', 'lose': 'lost', 'hear ': ''}.items():
    for f in forms.split(): IRR[f] = base
STOP = set('a an the of to or and in on at by for from with into upon as hence etc esp one oneself any thing things person persons something someone '
           'his her its their it him them out up down off away over back about after before again not no also'.split())
KEEP_PART = {'up', 'down', 'out', 'away', 'back', 'off', 'over', 'upon', 'forth'}
def stem(w):
    w = w.lower(); w = IRR.get(w, w)
    for suf in ('iest', 'ies', 'ied'):
        if w.endswith(suf) and len(w) > 5: return w[:-len(suf)] + 'y'
    for suf in ('eth', 'est', 'ing', 'ed', 'es', 's', 'e'):
        if w.endswith(suf) and len(w) - len(suf) >= 3: w = w[:-len(suf)]; break
    w = re.sub(r'our$', 'or', w)
    if len(w) > 3 and w[-1] == w[-2] and w[-1] not in 'ls': w = w[:-1]
    return w
def stems(text): return {stem(w) for w in re.findall(r"[a-z]+", text.lower()) if w not in STOP}
def same(a, b): return a == b or (len(a) >= 5 and len(b) >= 5 and a[:5] == b[:5])
def clean(s):
    s = re.sub(r'\s+', ' ', s.replace('\xad', '')).strip(' ,;:.')
    s = re.sub(r'^(?i:in (the )?LXX( and NT)?),?\s*', '', s)
    s = re.sub(r'^(to|I)\s+', '', s).replace(':', ',')
    s = ', '.join(re.sub(r'^(an?|to|the)\s+', '', p.strip()) for p in s.split(',') if p.strip() and stems(p))
    return s
def ok(s, lemma=''):
    if re.match(r'(?i)(he|she|it|they|we|you)\b', s) or re.search(r'\bnot\b', s): return False   # forms/negated fragments, not senses
    if re.match(r'be \w+ed\b', s) and not lemma.endswith('μαι'): return False                    # passive sense of an active verb
    return s and len(s) <= 70 and not re.search(r'[\u0370-\u03ff\u1f00-\u1fff]', s) and stems(s) and not re.match(r'(?i)(of|with|in|on|from|for|by)\b', s)
def dict_entry(dirn, k):
    try: return json.load(open(f'data/{dirn}/{k[:4]}.json')).get(k)
    except Exception: return None
AUX = {'be', 'hav', 'do', 'shall', 'will', 'let', 'may', 'thing'}   # Brenton auxiliaries/fillers: no sense evidence
# --- Brenton wording per lemma
BW = collections.defaultdict(collections.Counter)
for b in os.listdir('data/bw'):
    for f in os.listdir('data/bw/' + b):
        try: C = json.load(open(f'data/{b}/{f}'))
        except Exception: continue
        W = json.load(open(f'data/bw/{b}/{f}'))
        for v in C:
            m = W.get(v[0])
            if not m: continue
            for w, x in zip(v[1], m):
                if x:
                    st = stem(v[2][x[0]:x[1]])
                    if st not in AUX: BW[str(w[1])][st] += 1
def score(text, bc):
    st = stems(text); return sum(n for s, n in bc.items() if any(same(s, t) for t in st))
def trim(text, bc):
    parts = [p.strip() for p in re.split(r',\s*', text) if p.strip()]
    if len(parts) >= 3: parts = [p for p in parts if score(p, bc) > 0][:3] or parts
    text = ', '.join(parts)
    if len(text) <= 32 or len(parts) == 1: return text
    best = max(range(len(parts)), key=lambda i: (score(parts[i], bc), -i))
    keep = [parts[i] for i in range(len(parts)) if score(parts[i], bc) > 0][:3] or [parts[best]]
    return ', '.join(keep)
HAND = dict(l.rstrip('\n').split('\t') for l in open(os.path.join('..', 'tools', 'gloss_hand.tsv')) if '\t' in l and not l.startswith('#'))
out, review = {}, []
MINN, MIN_BEST, MAX_OLD = 6, 0.35, 0.10
for k, e in L.items():
    if e[2] not in POS: continue
    bc = BW.get(k, collections.Counter()); n = sum(bc.values()); freq = CNT.get(k, 0)
    old = e[1]; new, src = old, ''
    if n >= MINN and n >= 0.4 * freq and k not in GFIX and old:   # low coverage = Brenton mostly uses function words (e.g. πᾶς 'all'), no evidence
        s_old = score(old, bc) / n if stems(old) else 1.0   # e.g. 'be': nothing to compare -> keep
        cands = [(clean(p), 'LXX lexicon') for p in old.split(';')]
        d = dict_entry('dict', k)
        if d: cands += [(clean(d.get('g', '')), 'Abbott-Smith')] + [(clean(s), 'Abbott-Smith') for s in d.get('s', [])]
        d = dict_entry('lsj', k)
        if d: cands += [(clean(s), 'LSJ') for s in d.get('s', [])]
        cands = [(c, so) for c, so in cands if ok(c, e[0])]
        if cands:
            rank = {'LXX lexicon': 0, 'Abbott-Smith': 1, 'LSJ': 2}
            c, so = max(cands, key=lambda x: (score(x[0], bc), -rank[x[1]], -len(x[0])))
            sb = score(c, bc) / n
            top = [s for s, _ in bc.most_common(2)]
            if sb >= MIN_BEST and (s_old <= MAX_OLD or (sb >= 0.6 and sb >= 3 * s_old)) and so != 'LXX lexicon' or (so == 'LXX lexicon' and False):
                if any(any(same(s, t) for t in stems(c)) for s in top):
                    new = trim(c, bc); src = so
                    if new[:1].isupper() and new[1:2].islower(): new = new[0].lower() + new[1:]
                    first_old = clean(old.split(';')[0])
                    sq = lambda t: re.sub(r'[\W_]', '', t.lower()).replace('our', 'or')
                    if s_old >= 0.03 and sq(first_old) not in sq(new): new = new + '; ' + first_old
    if HAND.get(k) == 'KEEP': new, src = old, ''
    elif k in HAND:
        h = HAND[k]; pool = ' | '.join([old] + [x for dn in ('dict', 'lsj') for d in [dict_entry(dn, k) or {}] for x in [d.get('g', '')] + d.get('s', [])])
        assert all(part.strip() in pool for part in h.split(';')), ('hand sense not in licensed text', k, h)
        new, src = h, 'Abbott-Smith (hand-picked)'
    if re.sub(r'[\W_]', '', new.lower()) == re.sub(r'[\W_]', '', old.lower()): new, src = old, ''   # spelling-only change
    if new != old: out[k] = {'old': old, 'new': new, 'src': src}; e[1] = new
    review.append((k, e[0], freq, e[2], old, new, src, n, ', '.join(f'{w} {c}' for w, c in bc.most_common(5))))
json.dump(out, open('data/gloss_pick.json', 'w'), ensure_ascii=False, separators=(',', ':'))
json.dump(L, open('data/lexicon.json', 'w'), ensure_ascii=False, separators=(',', ':'))
review.sort(key=lambda r: -r[2])
sel = [r for r in review[:500]] + [r for r in review[500:] if r[4] != r[5] and r[2] >= 10]
with open(os.path.join('..', 'tools', 'gloss_review.tsv'), 'w') as f:
    f.write('# Automatic headline-gloss choice (tools/glosspick.py). Top 500 nouns/verbs/adjectives by frequency + every changed gloss with freq>=10.\n')
    f.write('lex\tlemma\tfreq\tpos\told_gloss\tnew_gloss\tnew_source\tbrenton_aligned\tbrenton_top_stems\tchanged\n')
    for r in sel: f.write('\t'.join(map(str, r)) + '\t' + ('yes' if r[4] != r[5] else '') + '\n')
print('glosspick: changed', len(out), 'of', sum(1 for e in L.values() if e[2] in POS), 'noun/verb/adj lemmas;',
      sum(1 for r in review if r[4] != r[5] and r[2] >= 10), 'changed with freq>=10; review rows', len(sel))

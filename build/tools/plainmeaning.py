#!/usr/bin/env python3
"""Plain-English headline meaning from general biblical-Greek dictionaries (not LXX-specific).
1. Dodson Greek-English Lexicon of the NT (Jeffrey Dodson; public domain / CC0, github.com/biblicalhumanities/Dodson-Greek-Lexicon), brief gloss.
2. Fallback: STEPBible TBESG brief gloss (STEP Bible, CC BY 4.0), already in data/dict.
3. Otherwise the previous headline (better-glosses: LXX lexicon gloss, hand-reviewed fix, or 'usual LXX sense').
Matching: Strong's number AND normalised lemma (NFC, accents/breathings stripped, final sigma, lower case), or normalised lemma alone.
Changes made to dictionary text (recorded as CC BY asks): whitespace tidied; leading 'I '/'to ' on verbs and 'a/an/the' on nouns removed;\nDodson's first-person 'am X' -> 'be X'; TBESG 'base: specific' reduced to the base gloss; a Dodson gloss with more than 3 senses or over 40\ncharacters is shortened to its first sense plus senses shared with the other sources (max 3; the full gloss stays under More). Nothing else.
lexicon.json entries become [lemma, headline, pos, translit, lsj, strong, src, alts]; src/alt codes: D Dodson, T STEP Bible (TBESG),
U usual LXX sense·automatic, H usual LXX sense·hand-picked, R LXX lexicon (corrected), L LXX lexicon.
Review list: tools/plain_review.tsv (500 most frequent LXX nouns/verbs/adjectives) with automatic flags."""
import json, os, re, unicodedata as u, collections, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, '..', 'site', 'data')
LP = f'{D}/lexicon.json'; BAK = os.path.join(HERE, '.lexicon_pre_plain.json')
L = json.load(open(LP))
if any(len(e) > 6 for e in L.values()): L = json.load(open(BAK))       # re-run: start again from the better-glosses lexicon
else: shutil.copy(LP, BAK)
CNT = json.load(open(f'{D}/counts.json')); GFIX = json.load(open(f'{D}/gloss_fixes.json')); GPICK = json.load(open(f'{D}/gloss_pick.json'))
def norm(s):
    s = ''.join(c for c in u.normalize('NFD', s) if not u.combining(c)).lower().replace('ς', 'σ')
    return u.normalize('NFC', re.sub(r'[^\w]', '', s))
def tidy(g, verb):
    g = re.sub(r'\s+', ' ', g or '').strip(' .;,')
    g = g.split(': ')[0]                                   # TBESG 'lord: God' = base gloss: specific sense -> base gloss
    parts = []
    for p in g.split(', '):
        p = re.sub(r'^I (?=[a-z])', '', p)
        p = re.sub(r'^to ', '', p) if verb else re.sub(r'^(a|an|the) ', '', p)
        p = re.sub(r'^am\b', 'be', p)                         # Dodson's 1st-person 'am able' -> 'be able'
        if p and p not in parts: parts.append(p)
    return ', '.join(parts)
def shorten(g, others):
    parts = g.split(', ')
    if len(parts) <= 3 and len(g) <= 40: return g
    ow = {w[:5] for w in re.findall(r'[a-z]{3,}', ' '.join(others).lower())}
    keep = [parts[0]] + [p for p in parts[1:] if {w[:5] for w in re.findall(r'[a-z]{3,}', p.lower())} & ow]
    for p in parts[1:]:
        if len(keep) >= 2: break
        if p not in keep: keep.append(p)
    keep = [p for p in parts if p in keep][:3]
    return ', '.join(keep)
# --- Dodson
DOD_S, DOD_L = {}, collections.defaultdict(list)
x = open('/workspace/src/dodson/dodson.xml', encoding='utf-8').read()
for m in re.finditer(r'<entry n="([^"|]+)\| (\d+)">.*?<def role="brief">(.*?)</def>', x, re.S):
    lem, st, g = m.group(1).strip(), 'G' + str(int(m.group(2))), re.sub(r'\s+', ' ', m.group(3)).strip()
    DOD_S[st] = (lem, g); DOD_L[norm(lem)].append((st, g))
def dict_g(k):
    try: return (json.load(open(f'{D}/dict/{k[:4]}.json')).get(k) or {}).get('g', '')
    except Exception: return ''
POS_CONTENT = ('Noun', 'Verbs', 'Adjective', 'Adverb')
stat = collections.Counter(); review = []
for k, e in L.items():
    verb = e[2] == 'Verbs'; B = e[1]
    bsrc = 'H' if k in GPICK and 'hand' in GPICK[k]['src'] else 'U' if k in GPICK else 'R' if k in GFIX else 'L'
    st = e[5] if re.match(r'^G\d+$', e[5] or '') else ''
    dg = ''
    if st and st in DOD_S and norm(DOD_S[st][0]) == norm(e[0]): dg = DOD_S[st][1]; stat['dodson strong+lemma'] += 1
    elif len(DOD_L.get(norm(e[0]), [])) == 1: dg = DOD_L[norm(e[0])][0][1]; stat['dodson lemma only'] += 1
    dg = tidy(dg, verb); tg = tidy(dict_g(k), verb)
    if 'Proper' in e[2]: dg = tg = ''                      # names: keep the lexicon form
    if dg: head, src = shorten(dg, [tg, B]), 'D'
    elif tg: head, src = tg, 'T'
    else: head, src = B, bsrc
    alts, seen = [], {norm(head)}
    cand = [(B, bsrc)]
    if bsrc in 'UH': cand.append((GPICK[k]['old'], 'L'))
    if bsrc == 'R': cand.append((GFIX[k]['old'], 'L'))
    cand += [(dg, 'D'), (tg, 'T')]   # full Dodson gloss kept if the headline was shortened
    for t, s in cand:
        if t and norm(t) not in seen: seen.add(norm(t)); alts.append([t, s])
    L[k] = e[:6] + [src, alts] if alts else e[:6] + [src]
    L[k][1] = head; stat['src ' + src] += 1
    review.append((k, e[0], CNT.get(k, 0), e[2], dg, tg, B, bsrc, head, src))
# --- hand-written override layer (tools/gloss_hand_plain.tsv; label W = 'hand-written'); the original wording stays under More
HW = {}
for l in open(os.path.join(HERE, 'gloss_hand_plain.tsv'), encoding='utf-8'):
    if '\t' in l and not l.startswith('#'):
        c = l.rstrip('\n').split('\t'); HW[norm(c[0])] = c
SRCN = {'Dodson': 'D', 'STEP Bible': 'T'}
hw_done = set()
for k, e in L.items():
    c = HW.get(norm(e[0]))
    if not c or 'Proper' in e[2]: continue
    lab, orig = c[2].split(': ', 1)
    old = [[e[1], e[6]]] + (e[7] if len(e) > 7 else [])
    alts, seen = [], {norm(c[1])}
    for t, sc in [[orig, SRCN.get(lab, e[6])]] + old:
        if norm(t) not in seen: seen.add(norm(t)); alts.append([t, sc])
    L[k] = e[:6] + ['W', alts]; L[k][1] = c[1]; hw_done.add(norm(e[0]))
    for i, r in enumerate(review):
        if r[0] == k: review[i] = r[:8] + (c[1], 'W')
assert hw_done == set(HW), ('hand-written lemmas not found', set(HW) - hw_done)
stat['hand-written'] = len(hw_done)
json.dump(L, open(LP, 'w'), ensure_ascii=False, separators=(',', ':'))
# --- review list with automatic flags
ARCH = set('thee thou thy thine ye hath doth shew shewn hearken hearkened unto wherefore whither thither smite smote begat ass beget wrought spake verily'.split())
def words(t): return set(re.findall(r'[a-z]+', t.lower()))
def stem(w): return w[:5]
FL = {}
for l in open(os.path.join(HERE, 'plain_flags.tsv'), encoding='utf-8'):
    if '\t' in l and not l.startswith('#'): a, b = l.rstrip('\n').split('\t'); FL[norm(a)] = b
top = [r for r in sorted(review, key=lambda r: -r[2]) if any(p in r[3] for p in POS_CONTENT[:3]) and 'Proper' not in r[3]][:500]
with open(os.path.join(HERE, 'plain_review.tsv'), 'w') as f:
    f.write('# Shown headline per lemma (tools/plainmeaning.py). Flags are automatic hints for review: archaic = old-fashioned English word; '
            'narrow = the shown dictionary gloss shares no word with the better-glosses (Brenton-based) headline; odd = very long or contains a note.\n')
    f.write('lex\tlemma\tfreq\tpos\tdodson\ttbesg\tbetter_glosses\tbetter_src\tshown\tshown_src\tflag\n')
    extra = [r for r in review if norm(r[1]) in FL and r not in top and 'Proper' not in r[3]]
    for r in top + extra:
        fl = ['hand: ' + FL[norm(r[1])]] if norm(r[1]) in FL else []
        if words(r[8]) & ARCH: fl.append('archaic')
        if r[9] in 'DT' and not ({stem(w) for w in words(r[8]) if len(w) > 2} & {stem(w) for w in words(r[6]) if len(w) > 2}): fl.append('narrow')
        if len(r[8]) > 45 or re.search(r'[()\[\]]|i\.e\.|e\.g\.', r[8]): fl.append('odd')
        f.write('\t'.join(map(str, r)) + '\t' + ','.join(fl) + '\n')
print('plainmeaning:', dict(stat))

"""Latin layer (study-bible-latin): Clementine Vulgate (eBible latVUC, PD) + Hetzenauer 1914 appendix (PD, transcribed here) + Douay-Rheims 1899 (eBible engDRA, PD),
LatinCy lemmas (MIT model) checked against Whitaker's Words (free for any use), Lewis & Short short meanings (Perseus, CC BY-SA 4.0: separate layer data/ls/),
verse pairing by content and open statistical Greek->Latin word matching. Inputs: LATIN_WORK (default /workspace/lxx-latin/work).
No NonCommercial data is read here (no PROIEL, no LemLat)."""
import json, os, re, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import latin_lemma as LL
W = os.environ.get('LATIN_WORK', '/workspace/lxx-latin/work'); HERE = os.path.dirname(os.path.abspath(__file__)); S = os.environ.get('SITE') or os.path.join(HERE, '..', '..')
D = os.path.join(S, 'data')
A_T = float(os.environ.get('ALIGN_T', '0.5'))
TAG = json.load(open(W + '/vul_tag2.json')); VM = json.load(open(W + '/vmap.json')); LS = json.load(open(W + '/ls_short.json'))
DR = json.load(open(W + '/dr.json')); AL = json.load(open(W + '/align_all.json'))
# Hetzenauer 1914 appendix (3-4 Esdras, Prayer of Manasseh). OFF by default: the transcription is unproofread OCR with verses missing
# (see completion-draft README). Turn on only after a proofread file replaces work/app_tag.json: LATIN_APPENDIX=1.
APPENDIX = os.environ.get('LATIN_APPENDIX') == '1'
if APPENDIX:
    TAG.update(json.load(open(W + '/app_tag.json')))
    if os.path.exists(W + '/app_vmap.json'): VM.update(json.load(open(W + '/app_vmap.json')))
    if os.path.exists(W + '/app_align.json'): AL += json.load(open(W + '/app_align.json'))
SUMMARY = os.environ.get('LATIN_SUMMARY') or os.path.join(W, 'build_latin_summary.json')
HAND = {}   # key -> hand-checked short meaning (latin_gloss_hand.tsv)
# Automatic Lewis & Short extracts are often a root sense, a grammar note or the wrong homograph (dĭco 'dedicate' for dīco 'say').
# Accuracy first: an automatic extract is shown only if it passes these checks; otherwise the card shows the headword + L&S link, no meaning.
GRAMNOTE = re.compile(r"^(-|pron|interrog|imp|impers|futur|pluperf|perf|ind|subj|prep|adv|adj|dem|demonstr|substantives?|dat|abl|gen|acc|nom|kindred|cf|v|sc|lit|init|or rather|dativ|pte|met|object)", re.I)
def auto_gloss(k):
    es = [x for x in LS[k] if x['g']]
    if len(es) != 1: return ''                       # several glossed homographs under one key: cannot tell which one the Vulgate means
    keep = []
    for g in es[0]['g']:
        g = g.strip().rstrip(';,.')
        if not g or len(g) > 40 or GRAMNOTE.match(g) or re.search(r'[ăĕĭŏŭāēīōūȳ^]', g) or not re.search(r'[a-z]{3}', g) or not g[0].isascii(): continue
        if re.match(r'^[A-Z][a-z]+$', g) and g.lower() not in ('god', 'lord'): g = g.lower()
        return g                                     # first clean sense only: later L&S 'senses' are often idioms or quotations
    return ''
# Measured on a token-weighted sample: about 1 in 8 automatic first senses is still wrong (e.g. nam 'for example', apostolus 'a notice sent
# to a higher tribunal'). So automatic meanings are OFF by default (LS_AUTO=1 turns them on); the candidates are written to a review list
# for the Latin Tutor, and reviewed lines go into latin_gloss_hand.tsv.
LS_AUTO = os.environ.get('LS_AUTO') == '1'
REVIEW = []
hp = os.path.join(HERE, 'latin_gloss_hand.tsv')
if os.path.exists(hp):
    for line in open(hp, encoding='utf-8'):
        if line.strip() and not line.startswith('#'): k, g = line.rstrip('\n').split('\t')[:2]; HAND[k] = g
def dr_clean(s): return re.sub(r'\s+([,.;:!?’”)])', r'\1', re.sub(r'([(“‘])\s+', r'\1', s)).strip()
def disp(s): return re.sub(r'\s+', ' ', s.replace('[', '').replace(']', '')).strip()
lemmas = {}; lemlist = []; morphs = {}; mlist = []; lsidx = {}; lslist = []; stats = collections.Counter()
def lem_id(l, pos, k):
    key = l + '|' + pos
    if key not in lemmas:
        li = -1
        if k:
            if k not in lsidx:
                e = [x for x in LS[k] if x['g']][0]; lsidx[k] = len(lslist)
                g = HAND.get(k) or ''
                if not g:
                    ag = auto_gloss(k)
                    if ag: REVIEW.append([k, e['hw'], ag])
                    if LS_AUTO: g = ag
                lslist.append([e['hw'], g, 1 if k in HAND else 0])
                stats['ls_hand' if k in HAND else 'ls_auto' if g else 'ls_nogloss'] += 1
            li = lsidx[k]
        lemmas[key] = len(lemlist); lemlist.append([l, pos, li])
    return lemmas[key]
def m_id(pos, m):
    key = pos + '|' + m
    if key not in morphs: morphs[key] = len(mlist); mlist.append(key)
    return morphs[key]
SHOWN = {}   # vkey -> list of show flags per word
VUL = collections.defaultdict(dict)   # (VB, ch) -> {v: [latin, dr, toks]}
occ = collections.defaultdict(list); cnt = collections.Counter()
for vk, (text, rec) in TAG.items():
    vb, c, v = vk.split('|')
    toks = []; sh = []
    for form, lemma, pos, morph, score in rec:
        l, p, k, show = LL.judge(form, lemma, pos, score, LS)
        stats['words'] += 1; stats['show%d' % show] += 1; sh.append(show)
        if show == 0: toks.append([form]); continue   # hidden: the word is shown, no lemma or meaning is guessed
        li = lem_id(LL.n(l) if p != 'PROPN' else l, p, k if show == 2 else '')
        toks.append([form, li, m_id(p, morph)])
        cnt[li] += 1
        if len(occ[li]) < 200 and (not occ[li] or occ[li][-1] != vk): occ[li].append(vk)
    SHOWN[vk] = sh
    VUL[(vb, int(c))][v] = [disp(text), dr_clean(DR.get(vb, {}).get(c + '|' + v, '')), toks]
def wjson(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(obj, open(path, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
import shutil
for d in ('vul', 'vp', 'ls', 'latocc'):
    shutil.rmtree(os.path.join(D, d), ignore_errors=True)
for (vb, c), vs in VUL.items():
    wjson(f'{D}/vul/{vb}/{c}.json', sorted(([int(v)] + x for v, x in vs.items()), key=lambda r: r[0]))
# pairing + alignment per our chapter
VP = collections.defaultdict(dict)
for k, (vk, s) in VM.items():
    b, c, v = k.split('|'); vb, vc, vv = vk.split('|'); VP[(b, c)][v] = [vb, int(vc), int(vv), {}]
ashown = collections.Counter(); acand = collections.Counter()
for a in AL:
    k, wi, li, conf, part = a[0], a[1], a[2], a[8], a[-1]
    b, c, v = k.split('|'); e = VP.get((b, c), {}).get(v)
    if not e: continue
    acand[part] += 1
    vk = '%s|%d|%d' % (e[0], e[1], e[2]); sh = SHOWN.get(vk)
    if conf < A_T or not sh or li >= len(sh) or sh[li] == 0: continue
    e[3][str(wi)] = li; ashown[part] += 1
for (b, c), vs in VP.items(): wjson(f'{D}/vp/{b}/{c}.json', vs)
wjson(f'{D}/latlex.json', lemlist); wjson(f'{D}/latmorph.json', mlist)
for i in range(0, len(lslist), 500): wjson(f'{D}/ls/{i // 500}.json', {str(j): lslist[j] for j in range(i, min(i + 500, len(lslist)))})
wjson(f'{D}/latsearch.json', [[LL.n(lemlist[i][0]), i, n] for i, n in cnt.most_common()])
for i in range(0, len(lemlist), 500):
    wjson(f'{D}/latocc/{i // 500}.json', {str(j): occ[j] for j in range(i, min(i + 500, len(lemlist))) if j in occ})
summ = {'words': stats['words'], 'lemma_meaning_shown': stats['show2'], 'name_shown': stats['show1'], 'hidden': stats['show0'],
        'align_threshold': A_T, 'align_candidates': dict(acand), 'align_shown': dict(ashown), 'lemmas': len(lemlist), 'ls_entries': len(lslist), 'verse_pairs': len(VM),
        'ls_hand': stats['ls_hand'], 'ls_auto': stats['ls_auto'], 'ls_nogloss': stats['ls_nogloss'], 'appendix': APPENDIX}
json.dump(summ, open(SUMMARY, 'w'), indent=1)
with open(os.path.splitext(SUMMARY)[0] + '_ls_review.tsv', 'w', encoding='utf-8') as f:   # build output for review, not shipped
    f.write('# key\theadword\tautomatic first sense\ttokens\n')
    ktok = collections.Counter()
    for li, nn in cnt.items():
        if lemlist[li][2] >= 0: ktok[lslist[lemlist[li][2]][0]] += nn
    for k, hw, g in sorted(REVIEW, key=lambda r: -ktok[r[1]]): f.write(f'{k}\t{hw}\t{g}\t{ktok[hw]}\n')
print(summ)
# ---- which Vulgate chapter(s) the Latin modes show for each of our chapters ----
BOOKS = json.load(open(f'{D}/books.json'))
VB = {'Gen': 'GEN', 'Exod': 'EXO', 'Lev': 'LEV', 'Num': 'NUM', 'Deut': 'DEU', 'Josh': 'JOS', 'Judg': 'JDG', 'Ruth': 'RUT', '1Sam': '1SA', '2Sam': '2SA', '1Kgs': '1KI', '2Kgs': '2KI', '1Chr': '1CH', '2Chr': '2CH',
      'Esth': 'EST', 'Job': 'JOB', 'Ps': 'PSA', 'Prov': 'PRO', 'Eccl': 'ECC', 'Song': 'SNG', 'Isa': 'ISA', 'Jer': 'JER', 'Lam': 'LAM', 'Ezek': 'EZK', 'Dan': 'DAN', 'Hos': 'HOS', 'Joel': 'JOL', 'Amos': 'AMO', 'Obad': 'OBA',
      'Jonah': 'JON', 'Mic': 'MIC', 'Nah': 'NAM', 'Hab': 'HAB', 'Zeph': 'ZEP', 'Hag': 'HAG', 'Zech': 'ZEC', 'Mal': 'MAL', 'Tob': 'TOB', 'Jdt': 'JDT', 'Wis': 'WIS', 'Sir': 'SIR', 'Bar': 'BAR', '1Macc': '1MA', '2Macc': '2MA',
      'Matt': 'MAT', 'Mark': 'MRK', 'Luke': 'LUK', 'John': 'JHN', 'Acts': 'ACT', 'Rom': 'ROM', '1Cor': '1CO', '2Cor': '2CO', 'Gal': 'GAL', 'Eph': 'EPH', 'Phil': 'PHP', 'Col': 'COL', '1Thess': '1TH', '2Thess': '2TH',
      '1Tim': '1TI', '2Tim': '2TI', 'Titus': 'TIT', 'Phlm': 'PHM', 'Heb': 'HEB', 'Jas': 'JAS', '1Pet': '1PE', '2Pet': '2PE', '1John': '1JN', '2John': '2JN', '3John': '3JN', 'Jude': 'JUD', 'Rev': 'REV',
      '1Esdr': 'ES3', '4Esdr': 'ES4', 'PrMan': 'MAN'}
have = collections.defaultdict(set)
for (vb, c) in VUL: have[vb].add(c)
vm = {}; used = set()
for b in BOOKS:
    bid = b['id']; chs = [c for c in b['chapters'] if isinstance(c, int)]
    for c in chs:
        if bid == '2Esdr': L = [['EZR', c]] if c <= 10 else [['NEH', c - 10]]
        elif bid == 'Sus': L = [['DAN', 13]]
        elif bid == 'Bel': L = [['DAN', 14]]
        elif bid == 'EpJer': L = [['BAR', 6]]
        elif bid == 'Joel': L = {1: [['JOL', 1]], 2: [['JOL', 2]], 3: [], 4: [['JOL', 3]]}[c]
        elif bid == 'Prov' and c == 31: L = [['PRO', 30], ['PRO', 31]]   # our Prov has no chapter 30 (LXX order)
        elif bid in VB: L = [[VB[bid], c]]
        else: L = []
        L = [x for x in L if x[1] in have.get(x[0], ())]
        vm[f'{bid}/{c}'] = L; used.update((x[0], x[1]) for x in L)
    if bid in VB and chs and bid not in ('Dan', 'Bar'):   # Vulgate chapters with no chapter of ours: shown after our last chapter
        extra = sorted(c for c in have.get(VB[bid], ()) if (VB[bid], c) not in used and c > chs[-1])
        vm[f'{bid}/{chs[-1]}'] += [[VB[bid], c] for c in extra]; used.update((VB[bid], c) for c in extra)
miss = sorted(f'{vb} {c}' for (vb, c) in VUL if (vb, c) not in used)
wjson(f'{D}/vulmap.json', vm); print('vulmap: Vulgate chapters not reachable:', miss)

"""Latin pass v2 (Gallicantus batch): per-token Latin card fills -> data/lcx/<VB>/<ch>.json (offline layer, read by latinChapter / onLatWord).
Input: the v2 proposal in /workspace/lxx-latin/latin-blanks/pass/v2/ (final_rows.pkl = the rows of part1..part6 TSVs incl. Tutor-applied values;
part1_quae_option.tsv). Each row is located in data/vul by its verse ref, form, token state and its global token number (consecutive within a verse).
Applied: verdict fill / fill_same_meaning / link, with no flag. Held (left blank): probable (neighbour check, invalid headword), blank, both, flagged.
quæ: every quæ token -> qui, 'who, which, that' (one combined meaning); the 79 hand-marked questions -> 'what? which? who?'.
Entry: [kind, lemma, text, li, whitaker]  kind c = meaning from context, l = dictionary meaning (L&S, via li), n = name (text = KJV spelling as printed
in the same verse, hyphens kept), q = quæ. li = data/latlex.json index when the lemma is an app lemma (lemma then left empty: it is read from latlex), else -1. whitaker = 1 when the headword is a
Whitaker's Words headword not in Lewis & Short. Usage: python3 build/tools/build_lcx.py"""
import csv, collections, json, os, pickle, unicodedata
SITE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
D = os.path.join(SITE, 'data'); V2 = '/workspace/lxx-latin/latin-blanks/pass/v2/'
R = pickle.load(open(V2 + 'final_rows.pkl', 'rb'))
Q = list(csv.DictReader(open(V2 + 'part1_quae_option.tsv', encoding='utf-8'), delimiter='\t'))
LATLEX = json.load(open(D + '/latlex.json', encoding='utf-8'))
def fold(s): return ''.join(c for c in unicodedata.normalize('NFD', (s or '').lower()) if not unicodedata.combining(c)).replace('æ', 'ae').replace('œ', 'oe').replace('j', 'i').replace('v', 'u')
BY = collections.defaultdict(list)
for i, x in enumerate(LATLEX): BY[fold(x[0])].append(i)
def lookup(lemma, name):
    c = BY.get(fold(lemma), [])
    pref = [i for i in c if (LATLEX[i][1] == 'PROPN') == name]
    return (pref or c or [-1])[0]
# locate rows: verse ref + global token number (consecutive within a verse) + form + state (cat u = no lemma in the app)
cache = {}
def verse(vb, c, v):
    if (vb, c) not in cache:
        p = f'{D}/vul/{vb}/{c}.json'
        cache[(vb, c)] = {row[0]: row for row in json.load(open(p, encoding='utf-8'))} if os.path.exists(p) else {}
    return cache[(vb, c)].get(v)
byref = collections.defaultdict(list)
for k, r in enumerate(R): byref[r['ref']].append(k)
POS, amb, miss = {}, [], []
for ref, ks in byref.items():
    vb, c, v = ref.split(':'); row = verse(vb, int(c), int(v)); toks = row[3] if row else []
    ks.sort(key=lambda k: R[k]['ti']); t0 = R[ks[0]]['ti']
    def ok(o, k):
        j = o + R[k]['ti'] - t0
        return 0 <= j < len(toks) and toks[j][0] == R[k]['form'] and (len(toks[j]) < 3) == (R[k]['cat'] == 'u')
    offs = [o for o in range(len(toks)) if all(ok(o, k) for k in ks)]
    if len(offs) != 1: (amb if offs else miss).append(ref); continue
    for k in ks: POS[k] = (vb, int(c), int(v), offs[0] + R[k]['ti'] - t0)
assert not amb and not miss, (amb[:5], miss[:5])
qi = iter(Q); OUT = collections.defaultdict(lambda: collections.defaultdict(dict)); N = collections.Counter()
FILL = ('fill', 'fill_same_meaning', 'link')
for k, r in enumerate(R):
    vb, c, v, i = POS[k]; tok = verse(vb, c, v)[3][i]; cur_li = tok[1] if len(tok) > 2 else -1
    if r['sub'] == 'quae_held':
        q = next(qi); assert q['ref'] == r['ref'] and q['form'] == r['form']
        li = lookup('qui', False)
        OUT[(vb, c)][v][i] = ['q', 'qui', q['quae_gloss'], li, 0]; N['quae_' + q['quae_option']] += 1; continue
    if r['verdict'] not in FILL: N['held_' + r['verdict']] += 1; continue
    if r.get('flag'): N['held_flagged'] += 1; continue
    name = r.get('kind') == 'name'
    lem = r.get('lemma') or (LATLEX[cur_li][0] if cur_li >= 0 else '')
    li = cur_li if cur_li >= 0 and fold(LATLEX[cur_li][0]) == fold(lem) else lookup(lem, name)
    wh = 1 if 'Whitaker headword' in (r.get('note') or '') else 0
    if r['verdict'] == 'link' and li >= 0: e = ['l', lem, '', li, wh]; N['link'] += 1
    elif name: e = ['n', lem, r['display'], li, 0]; N['name_' + ('existing_card' if r['part'] == '2b' else 'new')] += 1
    else: e = ['c', lem, r['display'] or r['meaning'], li, wh]; N['context' + ('_tutor' if r.get('tutor') else '')] += 1; N['whitaker_headword'] += wh
    if li < 0: N['lemma_not_in_app_lexicon'] += 1
    if li >= 0 and fold(LATLEX[li][0]) == fold(e[1]): e[1] = ''   # lemma shown from latlex
    OUT[(vb, c)][v][i] = e
os.makedirs(D + '/lcx', exist_ok=True)
for (vb, c), d in OUT.items():
    os.makedirs(f'{D}/lcx/{vb}', exist_ok=True)
    json.dump({str(v): {str(i): e for i, e in sorted(x.items())} for v, x in sorted(d.items())}, open(f'{D}/lcx/{vb}/{c}.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
json.dump(sorted(f'{vb}/{c}' for vb, c in OUT), open(f'{D}/lcx/index.json', 'w'), separators=(',', ':'))   # chapters that have fills (no 404s)
N['tokens_filled'] = sum(len(x) for d in OUT.values() for x in d.values()); N['files'] = len(OUT)
json.dump(dict(sorted(N.items())), open(os.path.join(SITE, 'build', 'lcx_stats.json'), 'w'), indent=1)
print(json.dumps(dict(sorted(N.items())), indent=1))

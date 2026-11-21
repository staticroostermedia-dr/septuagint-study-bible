"""3 Esdras, 4 Esdras, Prayer of Manasseh (Vulgate appendix, Hetzenauer 1914) -> data/vul/ES3, ES4, MAN + data/vulmap.json + data/vp (Gallicantus batch).
Input: the Latin Tutor's proofread TSVs /workspace/lxx-latin/esdras-proof/tutor/{es3,es4,prman}_latin_kjv.corrected.tsv (ref, latin, kjv_english).
The rows are already cut to the KJV verse division (final). Rows: [verse, latin, kjv_english, tokens] (the English column holds the KJV Apocrypha,
not Douay-Rheims, which lacks these books). Words are linked to a Latin dictionary form only where the same written form is tagged one way in at
least 90% of its Vulgate occurrences (no new tagging); other words stay plain. 3 Esdras (app 1Esdr) and PrMan are paired with the Greek by verse
number (the KJV follows the Greek numbering; every pair checked by English word overlap, none below 25%). An empty Latin cell (3 Esd 8:40) stays empty.
Usage: python3 build/tools/build_esdras.py"""
import csv, collections, glob, json, os, re
SITE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'); D = os.path.join(SITE, 'data')
T = '/workspace/lxx-latin/esdras-proof/tutor/'
BOOKS = [('es3_latin_kjv.corrected.tsv', 'ES3', '1Esdr', True), ('es4_latin_kjv.corrected.tsv', 'ES4', '4Esdr', False), ('prman_latin_kjv.corrected.tsv', 'MAN', 'PrMan', True)]
# form -> (li, mi) from the tagged Vulgate
F = collections.defaultdict(collections.Counter)
for f in glob.glob(D + '/vul/*/*.json'):
    if os.path.basename(os.path.dirname(f)) in ('ES3', 'ES4', 'MAN'): continue
    for row in json.load(open(f, encoding='utf-8')):
        for t in row[3]: F[t[0]][(t[1], t[2]) if len(t) > 2 else None] += 1
def tag(form):
    for k in (form, form.lower(), form[:1].upper() + form[1:]):
        c = F.get(k)
        if c:
            (best, n), tot = c.most_common(1)[0], sum(c.values())
            return [form] + list(best) if best and n / tot >= 0.9 else [form]
    return [form]
WORD = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿæœÆŒ]+")
vm = json.load(open(D + '/vulmap.json', encoding='utf-8')); stats = {}
for fn, vb, bid, pair in BOOKS:
    ch = collections.defaultdict(list); n = linked = words = empty = 0
    for r in csv.DictReader(open(T + fn, encoding='utf-8'), delimiter='\t'):
        c, v = map(int, r['ref'].rsplit(' ', 1)[1].split(':')); lat = (r['latin'] or '').strip()
        toks = [tag(w) for w in WORD.findall(lat)]
        words += len(toks); linked += sum(1 for t in toks if len(t) > 2); empty += not lat; n += 1
        ch[c].append([v, lat, r['kjv_english'].strip(), toks])
    os.makedirs(f'{D}/vul/{vb}', exist_ok=True)
    for c, rows in ch.items():
        json.dump(rows, open(f'{D}/vul/{vb}/{c}.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
        vm[f'{bid}/{c}'] = [[vb, c]]
        if pair:   # Greek verse -> same-numbered Latin verse (content pairing checked); no word-level matches
            g = json.load(open(f'{D}/{bid}/{c}.json', encoding='utf-8')); have = {x[0] for x in rows}
            os.makedirs(f'{D}/vp/{bid}', exist_ok=True)
            json.dump({str(x[0]): [vb, c, int(x[0]), {}] for x in g if str(x[0]).isdigit() and int(x[0]) in have},
                      open(f'{D}/vp/{bid}/{c}.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    stats[bid] = {'verses': n, 'chapters': len(ch), 'words': words, 'words_linked': linked, 'empty_latin': empty}
json.dump(vm, open(D + '/vulmap.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(json.dumps(stats, indent=1))

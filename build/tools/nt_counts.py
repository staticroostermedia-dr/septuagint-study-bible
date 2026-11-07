#!/usr/bin/env python3
"""NT counts, forms and search index (idempotent; run after build_nt.py, in site/).
- data/forms/N.json: per lemma, 'f' stays LXX-only; 'nf' = NT forms [form, morphIdx, count, firstRef]; 'b' gets NT book counts (OT keys untouched).
- data/occnt/N.json: NT occurrences in the same format as data/occ ([count, 'Book|ch|v', ...]).
- data/ntcounts.json: NT count per lemma (data/counts.json stays LXX-only)."""
import json, os, collections
D = 'data'
books = json.load(open(os.path.join(D, 'books.json'))); NT = [b for b in books if b.get('nt')]; NTIDS = {b['id'] for b in NT}
forms = collections.defaultdict(collections.OrderedDict); bk = collections.defaultdict(collections.Counter)
occ = collections.defaultdict(list); cnt = collections.Counter()
for b in NT:
    for c in b['chapters']:
        for v in json.load(open(os.path.join(D, b['id'], '%s.json' % c))):
            seen = set()
            for w in v[1]:
                lid = w[1]
                if not lid: continue
                cnt[lid] += 1; bk[lid][b['id']] += 1
                k = (w[0], w[2]); f = forms[lid]
                if k not in f: f[k] = [w[0], w[2], 0, '%s|%s|%s' % (b['id'], c, v[0])]
                f[k][2] += 1
                if lid not in seen: seen.add(lid); occ[lid].append('%s|%s|%s' % (b['id'], c, v[0]))
buckets = collections.defaultdict(dict)
for fn in os.listdir(os.path.join(D, 'forms')):
    buckets[int(fn.split('.')[0])] = json.load(open(os.path.join(D, 'forms', fn)))
for d in buckets.values():   # clear any earlier NT merge
    for e in d.values():
        e.pop('nf', None)
        for k in list(e.get('b', {})):
            if k in NTIDS: del e['b'][k]
for lid in cnt:
    d = buckets[lid // 100]; e = d.setdefault(str(lid), {'f': [], 'b': {}})
    e['nf'] = sorted(forms[lid].values(), key=lambda x: -x[2]); e['b'].update(bk[lid])
for n, d in buckets.items(): json.dump(d, open(os.path.join(D, 'forms', '%d.json' % n), 'w'), ensure_ascii=False, separators=(',', ':'))
od = os.path.join(D, 'occnt'); os.makedirs(od, exist_ok=True)
for fn in os.listdir(od): os.remove(os.path.join(od, fn))
ob = collections.defaultdict(dict)
for lid, refs in occ.items(): ob[lid // 100][str(lid)] = [cnt[lid]] + refs
for n, d in ob.items(): json.dump(d, open(os.path.join(od, '%d.json' % n), 'w'), ensure_ascii=False, separators=(',', ':'))
json.dump({str(k): v for k, v in cnt.items()}, open(os.path.join(D, 'ntcounts.json'), 'w'), separators=(',', ':'))
print('NT lemmas', len(cnt), 'tokens', sum(cnt.values()), 'forms buckets', len(buckets), 'occnt buckets', len(ob))

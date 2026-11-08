#!/usr/bin/env python3
"""LXX2012 pop-up lines come ONLY from a reviewed allowlist (Greek Maestro's lxx2012_allowlist.json; this script never edits it).
Writes data/lx/index.json + data/lx/<Book>/<ch>.json = {verse: [text, label]}. If the file is missing or malformed, or an entry is invalid,
that entry (or everything) is left out and the problem is printed: no LXX2012 line is shown for it.
Usage: lxx2012_allow.py ALLOWLIST_JSON   (run in site/)"""
import json, os, shutil, sys
D = 'data'; out = {}; problems = []
shutil.rmtree(os.path.join(D, 'lx'), ignore_errors=True); os.makedirs(os.path.join(D, 'lx'))
try:
    A = json.load(open(sys.argv[1], encoding='utf-8'))
    if not isinstance(A, dict): raise ValueError('top level is not an object')
except Exception as e:
    A = {}; problems.append('allowlist missing or malformed: %s' % e)
books = {b['id']: b for b in json.load(open(os.path.join(D, 'books.json')))}
for bid, chs in A.items():
    for ch, vs in (chs.items() if isinstance(chs, dict) else []):
        for v, e in (vs.items() if isinstance(vs, dict) else []):
            ref = '%s %s:%s' % (bid, ch, v)
            if bid not in books or books[bid].get('nt') or not os.path.exists(os.path.join(D, bid, '%s.json' % ch)): problems.append(ref + ': no such OT chapter'); continue
            if not isinstance(e, dict) or not isinstance(e.get('text'), str) or not e['text'].strip(): problems.append(ref + ': no text'); continue
            if e.get('label') != 'alternate rendering': problems.append(ref + ': label is not "alternate rendering"'); continue
            vv = [x for x in json.load(open(os.path.join(D, bid, '%s.json' % ch))) if x[0] == str(v)]
            if not vv: problems.append(ref + ': no such verse'); continue
            out.setdefault(bid, {}).setdefault(str(ch), {})[str(v)] = [e['text'].strip(), e['label']]
            if e.get('brenton') and vv[0][2] and e['brenton'].strip() != vv[0][2].strip(): problems.append(ref + ': note: allowlist "brenton" differs from the Brenton shown (entry kept)')
idx = []
for bid, chs in out.items():
    os.makedirs(os.path.join(D, 'lx', bid), exist_ok=True)
    for ch, d in chs.items():
        json.dump(d, open(os.path.join(D, 'lx', bid, ch + '.json'), 'w'), ensure_ascii=False, separators=(',', ':')); idx.append(bid + '/' + ch)
json.dump(sorted(idx), open(os.path.join(D, 'lx', 'index.json'), 'w'))
print('allowlisted LXX2012 lines:', sum(len(d) for c in out.values() for d in c.values()), [f'{b} {c}:{v}' for b, cs in out.items() for c, d in cs.items() for v in d])
for p in problems: print('PROBLEM:', p)

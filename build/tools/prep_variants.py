"""Spelling-variant retry for forms Morpheus could not analyse (general rules, no per-word lists):
  -οσαν (Koine 3rd plural aorist/imperfect, e.g. ἤλθοσαν)  -> -ον, keep only 3rd-plural analyses
  -τωσαν (Koine 3rd plural imperative, e.g. γνώτωσαν)      -> -τω, analysis changed from 3rd singular to 3rd plural
  ᾖρ/ῇρ/ῄρ (αἴρω aorist written with iota subscript)      -> ἦρ/ῆρ/ήρ, keep only verb analyses
  ῇ/ῷ/ᾷ without subscript, or ῶ/ῆ/ᾶ with it (ζῇν, ἀθῶον)   -> the other spelling
  initial γἱ/νἱ (misprints of υἱ in the eBible text)        -> υἱ
Writes work/var.beta (Morpheus input) and work/var_map.json {variant_beta: [[form, rule], ...]}."""
import json, re, unicodedata as u
from greek import to_beta
W = '/workspace/lxx-cl/work'
def parsed(path):
    res, cur = {}, None
    for l in open(path, encoding='utf-8', errors='replace'):
        l = l.rstrip('\n')
        if l.startswith('<NL>'): res[cur] = 1
        elif l.strip() and not l.startswith(':'): cur = l.strip()
    return res
ok = parsed(W + '/morph.out'); ok.update(parsed(W + '/morph_n.out'))
forms = [f for f in open(W + '/forms.txt').read().split('\n') if f and to_beta(f) not in ok]
nfc = lambda s: u.normalize('NFC', s)
SW = {'ῇ': 'ῆ', 'ῷ': 'ῶ', 'ᾷ': 'ᾶ', 'ῆ': 'ῇ', 'ῶ': 'ῷ', 'ᾶ': 'ᾷ'}
def variants(f):
    f = nfc(f); out = []
    bare = ''.join(c for c in u.normalize('NFD', f) if not u.combining(c))
    if bare.endswith('οσαν') and len(bare) > 5: out.append((f[:-4] + 'ον', 'pl3'))
    if bare.endswith('τωσαν') and len(bare) > 6: out.append((f[:-5] + 'τω', 'imp_pl'))
    for a, b in (('ᾖρ', 'ἦρ'), ('ῇρ', 'ῆρ'), ('ῄρ', 'ήρ')):
        if a in f: out.append((f.replace(a, b), 'verb'))
    for i, c in enumerate(f):
        if c in SW: out.append((f[:i] + SW[c] + f[i + 1:], ''))
    for a in ('γἱ', 'νἱ'):
        if f.startswith(a): out.append(('υἱ' + f[2:], ''))
    return out
vm = {}
for f in forms:
    for v, r in variants(f): vm.setdefault(to_beta(v), []).append([f, r])
json.dump(vm, open(W + '/var_map.json', 'w'), ensure_ascii=False)
open(W + '/var.beta', 'w').write('\n'.join(sorted(vm)) + '\n')
print('forms without analysis', len(forms), 'variants', len(vm))

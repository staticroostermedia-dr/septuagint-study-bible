from greek import *
G = vpl(GRC); forms = set(); caps = set()
for t in G.values():
    for w in tokens(t):
        forms.add(lower_form(w)); a = acute(w)
        if is_cap(a): caps.add(to_beta_cap(a))
W = '/workspace/lxx-cl/work'
open(W + '/forms.txt', 'w').write('\n'.join(sorted(forms)))
open(W + '/forms.beta', 'w').write('\n'.join(to_beta(f) for f in sorted(forms)) + '\n')
open(W + '/caps.beta', 'w').write('\n'.join(sorted(caps)) + '\n')

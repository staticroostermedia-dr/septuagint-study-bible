import re
W = '/workspace/lxx-cl/work'; res = {}; cur = None
for l in open(W + '/morph.out', encoding='utf-8', errors='replace'):
    l = l.rstrip('\n')
    if l.startswith('<NL>'): res[cur] = 1
    elif l.strip() and not l.startswith(':'): cur = l.strip()
inp = open(W + '/forms.beta').read().split('\n')[:-1]
open(W + '/miss.beta', 'w').write('\n'.join(f for f in inp if f not in res) + '\n')

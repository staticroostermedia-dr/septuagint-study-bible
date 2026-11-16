"""Order the curated list (draft3.txt: ref|reason) into verses.tsv: line N = day N of a leap-year calendar.
Sections are interleaved in proportion (Septuagint / Apocrypha / NT, each in Bible order); a few dates are pinned."""
import json, re
L = [l.split('|', 1) for l in open('/workspace/lxx-latin/votd/draft3.txt').read().splitlines() if l.strip()]
APOC = {'Tob', 'Jdt', '1Macc', '2Macc', '3Macc', '4Macc', 'Wis', 'Sir', 'Bar', 'EpJer', 'Sus', 'Bel', '1Esdr', '4Esdr', 'PrMan'}
books = json.load(open('/workspace/lxx-nt/site/data/books.json')); order = [b['id'] for b in books]; NT = {b['id'] for b in books if b.get('nt')}
def sec(r):
    b, cv = r.split(); c = cv.split(':')[0]
    return 2 if b in NT else 1 if b in APOC or (b, c) in (('Ps', '151'), ('Dan', '3')) else 0
def key(r):
    b, cv = r.split(); c, v = cv.split(':'); m = re.match(r'(\d+)(\w*)', v); return (order.index(b), int(c), int(m.group(1)), m.group(2))
CUM = [0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]
def day(m, d): return CUM[m - 1] + d          # 1-based day of the leap-year calendar
pins = {day(1, 1): 'Gen 1:1', day(1, 2): 'John 1:1', day(2, 14): '1Cor 13:4', day(12, 23): 'Isa 7:14', day(12, 24): 'Luke 2:10',
        day(12, 25): 'Luke 2:14', day(12, 26): 'Luke 2:11', day(12, 31): 'Rev 21:5'}
byref = {x[0]: x for x in L}
S = [sorted([x for x in L if sec(x[0]) == i and x[0] not in pins.values()], key=lambda x: key(x[0])) for i in range(3)]
seq, k, tot = [], [0, 0, 0], [len(s) for s in S]
while sum(k) < sum(tot):
    i = min((j for j in range(3) if k[j] < tot[j]), key=lambda j: (k[j] + 0.5) / tot[j]); seq.append(S[i][k[i]]); k[i] += 1
for d in sorted(pins): seq.insert(d - 1, byref[pins[d]])
assert len(seq) == 366 and len({x[0] for x in seq}) == 366
assert all(seq[d - 1][0] == r for d, r in pins.items())
with open('/workspace/lxx-latin/votd/verses.tsv', 'w') as f:
    f.write('ref\treason\n')
    for x in seq: f.write(x[0] + '\t' + x[1] + '\n')
print('sections', [sum(1 for x in seq if sec(x[0]) == i) for i in range(3)])

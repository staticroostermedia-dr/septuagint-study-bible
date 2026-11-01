import json,random,sys
rows=[l.split('\t') for l in open('work/reseg_report.tsv').read().strip().split('\n')]
random.seed(int(sys.argv[1])); S=random.sample(rows,int(sys.argv[2])) if len(sys.argv)>2 else rows
for r in S:
    b,cv=r[0].split(' '); c,vv=cv.split(':'); a,z=vv.split('-')
    vs=json.load(open(f'site/data/{b}/{c}.json')); en=json.load(open(f'work/orig_en/{b}_{c}.json'))
    ids=[x[0] for x in vs]; i=ids.index(a)
    print('##',*r)
    for j in (i,i+1):
        print(f'  {ids[j]} G: '+' '.join(t[0] for t in vs[j][1])[-90:] if j==i else f'  {ids[j]} G: '+' '.join(t[0] for t in vs[j][1])[:90])
        print('     old: '+((en[j] or '')[-110:] if j==i else (en[j] or '')[:110]))
        print('     new: '+((vs[j][2] or '')[-110:] if j==i else (vs[j][2] or '')[:110]))

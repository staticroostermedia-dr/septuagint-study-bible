"""Whitaker's Words (free for any use) - lightweight analyser: form -> set of (POS, stem1, decl/conj) from DICTLINE.GEN + INFLECTS.LAT."""
import re,collections
import os
W=os.environ.get('WHITAKER','/workspace/lxx-latin/src/whitaker/')
def n(s): return s.lower().replace('v','u').replace('j','i')
ENT=[]; IDX=collections.defaultdict(list)
for line in open(W+'DICTLINE.GEN',encoding='latin-1'):
    if len(line)<80: continue
    stems=[n(line[i*19:(i+1)*19].strip()) for i in range(4)]
    rest=line[76:].split()
    if not rest: continue
    pos=rest[0]; a=int(rest[1]) if len(rest)>1 and rest[1].isdigit() else 0; b=int(rest[2]) if len(rest)>2 and rest[2].isdigit() else 0
    e=(pos,a,b,stems[0],line[110:].strip()[:60] if len(line)>110 else '')
    ENT.append(e)
    for k,s in enumerate(stems):
        if s and s!='zzz': IDX[(k+1,s)].append(len(ENT)-1)
INF=[]
pat=re.compile(r'(\d) (\d+) ?(\S*)\s+[A-Z] [A-Z]\s*$')
for line in open(W+'INFLECTS.LAT',encoding='latin-1'):
    line=line.split('--')[0]
    if not line.strip(): continue
    t=line.split(); pos=t[0]
    m=pat.search(line)
    if not m: continue
    a=int(t[1]) if t[1].isdigit() else 0; b=int(t[2]) if len(t)>2 and t[2].isdigit() else 0
    k,ln,end=int(m.group(1)),int(m.group(2)),n(m.group(3)) if int(m.group(2)) else ''
    INF.append((pos,a,b,k,end))
BYEND=collections.defaultdict(list)
for x in INF: BYEND[x[4]].append(x)
UNI=collections.defaultdict(set)
lines=open(W+'UNIQUES.LAT',encoding='latin-1').read().split('\n')
for i in range(0,len(lines)-2,3):
    if lines[i].strip(): UNI[n(lines[i].strip())].add(lines[i+1].split()[0] if lines[i+1].split() else '')
FAM={'VPAR':'V','SUPINE':'V'}
def analyse(form):
    f=n(form); res=set()
    for x in UNI.get(f,()): res.add((x,'',f))
    for cut in range(0,min(len(f),9)):
        end=f[len(f)-cut:] if cut else ''; stem=f[:len(f)-cut]
        for pos,a,b,k,e in BYEND.get(end,()):
            P=FAM.get(pos,pos)
            for ei in IDX.get((k,stem),()):
                ep,ea,eb,s1,_=ENT[ei]
                if ep!=P and not (P=='ADJ' and ep=='ADJ'): continue
                if a and ea and a!=ea: continue
                if b and eb and b!=eb and not(P=='V'): continue
                res.add((ep,s1,str(ea)))
    # indeclinables stored with full stem
    for ei in IDX.get((1,f),()):
        ep=ENT[ei][0]
        if ep in('ADV','PREP','CONJ','INTERJ') : res.add((ep,ENT[ei][3],''))
    return res
def analyse_enc(form):
    r=analyse(form)
    if not r:
        f=n(form)
        for enc in('que','ne','ue'):
            if f.endswith(enc) and len(f)>len(enc)+1: r=analyse(f[:-len(enc)]); 
            if r: break
    return r
UDMAP={'NOUN':{'N'},'PROPN':{'N'},'VERB':{'V'},'AUX':{'V'},'ADJ':{'ADJ','NUM','V'},'DET':{'PRON','ADJ','NUM'},'PRON':{'PRON'},'ADV':{'ADV','ADJ'},'ADP':{'PREP'},'CCONJ':{'CONJ'},'SCONJ':{'CONJ','ADV'},'PART':{'ADV','CONJ'},'NUM':{'NUM','ADJ'},'INTJ':{'INTERJ'}}
IRREG={"sum","possum","eo","fero","uolo","nolo","malo","fio","adsum","absum","prosum","desum","obsum","praesum","subsum","supersum","intersum","inquam","aio","edo","queo","nequeo"}
def agree(form,lemma,upos):
    """True = Whitaker supports LatinCy's lemma+POS; False = disagrees; None = Whitaker doesn't know the form."""
    L=n(lemma)
    if L in IRREG and upos in('VERB','AUX'): return True
    r=analyse_enc(form)
    if not r: return None
    ok=UDMAP.get(upos,set())
    for ep,s1,_ in r:
        if ep not in ok and not (upos in('PRON','DET') and ep=='PRON'): continue
        if ep=='PRON' and upos in('PRON','DET'): return True
        if not s1: return True
        if L.startswith(s1) and len(L)-len(s1)<=4: return True
        if s1.startswith(L) and len(s1)-len(L)<=1: return True
    return False
if __name__=='__main__':
    for f,l,p in [('dixit','dico','VERB'),('salutari','saluto','VERB'),('salutari','salutaris','NOUN'),('Do','Do','PROPN'),('do','do','VERB'),('eo','eo','PRON'),('eo','is','PRON'),('lux','lux','NOUN'),('est','sum','AUX'),('altare','altare','NOUN'),('coepit','coepi','VERB'),('reuersus','reuertor','VERB'),('unamque','unus','DET'),('et','et','CCONJ'),('Abraham','Abraham','PROPN'),('principio','principium','NOUN'),('erat','sum','AUX'),('uidit','uideo','VERB'),('filios','filius','NOUN')]:
        print(f,l,p,agree(f,l,p),sorted(analyse_enc(f))[:4])

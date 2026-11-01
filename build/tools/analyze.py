#!/usr/bin/env python3
"""Lemma + morphology candidates for every Brenton-Greek form, from clean sources only.
Routes, in order (source letter kept per form):
  M  Morpheus (perseids-tools/morpheus, MPL-2.0; run locally, its output analyses are used, Morpheus itself is not shipped)
  N  Morpheus accent-insensitive (-n), only where the analysis differs from the form by diacritics alone
  T  STEPBible TAGNT surface form -> lemma/morph (CC BY 4.0)
  H  form equals a dictionary headword (STEPBible TBESG / TFLSJ, CC BY 4.0; Dodson PD/CC0)
  K  Wiktionary form-of / inflection tables via kaikki.org (CC BY-SA 4.0) -- separate layer
Output work/analysis.json  {lowerform: {"src": X, "c": [[lemma, code, weight], ...]}}"""
import json, re, sys, os, math, collections, unicodedata as u
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from greek import *
W = '/workspace/lxx-cl/work'
# ---------------- dictionaries (headwords) ----------------
HW = collections.defaultdict(list)   # norm -> [(strong, lemma, posc, src)]
TB = {}
for l in open('/workspace/lxx-audit/src/tbesg.txt', encoding='utf-8'):
    r = l.rstrip('\n').split('\t')
    if len(r) < 8 or not re.match(r'G\d', r[0]): continue
    st = re.match(r'G\d+', r[0]).group()
    TB.setdefault(st, (r[3], r[5], r[6]))
    HW[norm(r[3])].append((st, r[3], r[5], 'T'))
for f in ('tflsj1.txt', 'tflsj2.txt'):
    for l in open('/workspace/src/' + f, encoding='utf-8'):
        r = l.rstrip('\n').split('\t')
        if len(r) < 8 or not re.match(r'G\d', r[0]): continue
        st = re.match(r'G\d+', r[0]).group()
        if not any(x[0] == st for x in HW[norm(r[3])]): HW[norm(r[3])].append((st, r[3], r[5], 'L'))
x = open('/workspace/src/dodson/dodson.xml', encoding='utf-8').read()
for m in re.finditer(r'<entry n="([^"|]+)\| (\d+)">', x):
    lem, st = m.group(1).strip(), 'G%04d' % int(m.group(2))
    if not any(e[0] == st for e in HW[norm(lem)]): HW[norm(lem)].append((st, lem, '', 'D'))
def headword(lem):
    """dictionary spelling of a lemma: exact accented match first, else unique accent-insensitive match"""
    c = HW.get(norm(lem), [])
    ex = [e for e in c if acute(e[1]).lower() == acute(lem).lower()]
    return (ex or c or [None])[0]
# Morpheus (Attic) lemma -> Koine dictionary lemma
KOINE = [('γιγν', 'γιν'), ('ττ', 'σσ'), ('ρρ', 'ρσ')]
SPECIAL = {'εἶπον': 'εἶπον'}
# Morpheus lemma -> the NT/LXX dictionary (TBESG/Dodson) headword for the same verb or noun. Morpheus names some words by a poetic, Ionic
# or principal-part form that the NT/LXX dictionaries do not list, so the card would show no meaning. Only pairs checked by hand in LSJ.
ALIAS = {'εἶδον': 'εἴδω', 'Βορέας': 'βορρᾶς', 'ἀφεστήξω': 'ἀφίστημι', 'συνόχωκα': 'συνέχω', 'ἀείδω': 'ᾄδω', 'ψεύδω': 'ψεύδομαι', 'οἰκτειρέω': 'οἰκτείρω',
         'ἀνοίγνυμι': 'ἀνοίγω', 'ἀρνός': 'ἀρήν', 'περιζώννυμαι': 'περιζώννυμι', 'σαυτοῦ': 'σεαυτοῦ'}
ASUF = [('πίτνω', 'πίπτω'), ('λιμπάνω', 'λείπω')]   # poetic present stems -> the Koine verb (ἐμπίτνω -> ἐμπίπτω)
def dict_lemma(lem):
    if lem in ALIAS: return ALIAS[lem]
    for a, b in ASUF:
        if lem.endswith(a) and headword(lem[:-len(a)] + b): return headword(lem[:-len(a)] + b)[1]
    if ', ' in lem:   # TAGNT lists spelling variants 'Δαυείδ, Δαυίδ, Δαβίδ'
        vs = lem.split(', '); lem = next((v for v in vs if headword(v)), vs[0])
    for a, b in KOINE + [('γίγν', 'γίν'), ('ίγν', 'ίν')]:   # prefer the Koine spelling when a NT/LXX dictionary (TBESG/Dodson) has it
        if a in lem:
            h = headword(lem.replace(a, b, 1))
            if h and h[3] in 'TD': return h[1]
    if headword(lem): return headword(lem)[1]
    return lem
# ---------------- compound composition (Morpheus 'dia/-ka/mptw') ----------------
PRE = {'a)mfi/': 'ἀμφι', 'a)na/': 'ἀνα', 'a)nti/': 'ἀντι', 'a)po/': 'ἀπο', 'dia/': 'δια', 'e)k': 'ἐκ', 'e)c': 'ἐκ', 'e)n': 'ἐν', 'ei)s': 'εἰσ', 'e)pi/': 'ἐπι',
       'kata/': 'κατα', 'meta/': 'μετα', 'para/': 'παρα', 'peri/': 'περι', 'pro/': 'προ', 'pro/s': 'προσ', 'su/n': 'συν', 'u(pe/r': 'ὑπερ', 'u(po/': 'ὑπο',
       'e)pi': 'ἐπι', 'a)po': 'ἀπο', 'para': 'παρα', 'kata': 'κατα', 'dia': 'δια', 'a)na': 'ἀνα', 'u(po': 'ὑπο', 'meta': 'μετα', 'a)nti': 'ἀντι', 'peri': 'περι', 'pro': 'προ', 'e)cw': 'ἐξω'}
ASP = {'π': 'φ', 'τ': 'θ', 'κ': 'χ'}
VOW = 'αεηιουωᾳῃῳ'
def strip_marks(s): return ''.join(c for c in u.normalize('NFD', s) if not u.combining(c))
def join(pre, base):
    p = strip_marks(from_beta(pre)) if pre in PRE or True else pre
    p = PRE.get(pre, p); p = u.normalize('NFC', p)
    bd = u.normalize('NFD', base); rough = '\u0314' in bd[:3]
    b0 = strip_marks(base[0]); bvow = b0 in 'αεηιουω'
    # remove the base's breathing
    bn = u.normalize('NFC', bd.replace('\u0313', '').replace('\u0314', '', 1) if bvow else bd)
    pl = strip_marks(p)
    if bvow:
        if pl in ('εκ',): p = p[:-1] + 'ξ'
        elif pl[-1] in 'αιο' and pl not in ('περι', 'προ'): p = p[:-1]
        if rough and strip_marks(p[-1]) in ASP: p = p[:-1] + ASP[strip_marks(p[-1])]
    elif pl in ('συν', 'εν'):
        if b0 in 'βπφψμ': p = p[:-1] + 'μ'
        elif b0 in 'γκχξ': p = p[:-1] + 'γ'
        elif b0 in 'λρ': p = p[:-1] + b0
        elif b0 == 'σ' and pl == 'συν': p = p[:-1]
    # keep the prefix's breathing, drop its accent
    p = u.normalize('NFC', u.normalize('NFD', p).replace('\u0301', '').replace('\u0300', ''))
    return u.normalize('NFC', p + bn)
def lemma_of(field):
    segs = field.split(',')
    if len(segs) > 1 and segs[0] in PRE and '-' in segs[-1]: pre, last = segs[:-1], segs[-1]
    else: pre, last = [], segs[-1]
    if last.endswith('-pl'): last = last[:-3]
    parts = last.split('-'); pre = pre + parts[:-1]
    w = from_beta(parts[-1])
    for p in reversed(pre): w = join(p, w)
    return re.sub(r'\d', '', w)
# ---------------- Morpheus output -> codes ----------------
T = {'pres': 'P', 'imperf': 'I', 'fut': 'F', 'aor': 'A', 'perf': 'X', 'plupf': 'Y', 'futperf': 'F'}
V = {'act': 'A', 'mid': 'M', 'pass': 'P', 'mp': 'E'}
MO = {'ind': 'I', 'subj': 'S', 'opt': 'O', 'imperat': 'D', 'inf': 'N', 'part': 'P'}
C = {'nom': 'N', 'gen': 'G', 'dat': 'D', 'acc': 'A', 'voc': 'V'}
NU = {'sg': 'S', 'pl': 'P', 'dual': 'D'}
GE = {'masc': 'M', 'fem': 'F', 'neut': 'N'}
ADJ_ST = re.compile(r'^(os_h_on|os_a_on|os_on|us_eia_u|hs_es|wn_on|eis_essa_en|wn_ousa_on|as_aina_an|hs_es|ws_uia_os|ous_ousa_on|os_h_on|on_ousa_on|wn_on_comp|eis_esa_en|us_u|os_h_ov|h_on|w_n|pron_adj\d|art_adj|irreg_adj\d)')
def codes(pos, feats, stype, lem_tb_pos):
    """-> list of codes (several when Morpheus collapses cases/genders like nom/voc/acc)"""
    fs = feats.split(); out = []
    def multi(key, table):
        v = [x for x in fs if all(p in table for p in x.split('/'))]
        return [table[p] for p in v[0].split('/')] if v else ['']
    if pos in ('V', 'P'):
        t = [T[x] for x in fs if x in T]; vo = [V[x] for x in fs if x in V]; mo = [MO[x] for x in fs if x in MO]
        t = t[0] if t else 'P'; vo = vo[0] if vo else 'A'; mo = mo[0] if mo else 'I'
        if mo == 'P':
            for c in multi('c', C):
                for n in multi('n', NU):
                    for g in multi('g', GE): out.append(f'V.{t}{vo}P{c}{n}{g}')
        elif mo == 'N': out.append(f'V.{t}{vo}N')
        else:
            pe = [x[0] for x in fs if x in ('1st', '2nd', '3rd')]
            for n in multi('n', NU): out.append(f'V.{t}{vo}{mo}{pe[0] if pe else ""}{n}')
        return out
    if 'indeclform' in stype or not any(p in C for x in fs for p in x.split('/')):
        st = stype.split()[-1] if stype.split() else ''
        if 'adverbial' in fs: return ['D']
        m = {'prep': 'P', 'conj': 'C', 'adverb': 'D', 'particle': 'X', 'numeral': 'M', 'exclam': 'I', 'article': 'RA', 'relative': 'RR', 'indef': 'RI', 'indecl': 'RI', 'pron1': 'RP', 'pron3': 'RP', 'demonstr': 'RD'}.get(st)
        if m and not any(p in C for x in fs for p in x.split('/')): return [m]
        if not any(p in C for x in fs for p in x.split('/')): return ['N'] if not m else [m]
    st = stype.split()[-1] if stype.split() else ''
    pre = {'article': 'RA', 'relative': 'RR', 'indef': 'RI', 'indecl': 'RI', 'pron1': 'RP', 'pron3': 'RP', 'art_adj': 'RP', 'pron_adj1': 'RD', 'demonstr': 'RD'}.get(st)
    if not pre:
        if lem_tb_pos: pre = 'A' if lem_tb_pos[1:].startswith(':A') else 'N'
        else: pre = 'A' if ADJ_ST.match(st) else 'N'
    for c in multi('c', C):
        for n in multi('n', NU):
            for g in multi('g', GE): out.append(f'{pre}.{c}{n}{g}')
    return out
def parse_out(path):
    res, cur = {}, None
    for l in open(path, encoding='utf-8', errors='replace'):
        l = l.rstrip('\n')
        if l.startswith('<NL>'): res[cur] = re.findall(r'<NL>(.*?)</NL>', l)
        elif l.strip() and not l.startswith(':'): cur = l.strip(); res.setdefault(cur, [])
    return res
def analyses(lines):
    out = []
    for a in lines:
        m = re.match(r'(\S) (\S+) ?(.*)$', a)
        if not m: continue
        pos, field, rest = m.groups(); rest = rest[1:] if rest.startswith(' ') else rest
        cols = rest.split('\t'); feats = cols[0]; dial = cols[1] if len(cols) > 1 else ''; stype = '\t'.join(cols[2:])
        lem = dict_lemma(lemma_of(field))
        hwd = headword(lem)
        pen = 0
        if dial and 'attic' not in dial and 'koine' not in dial: pen += 1.5
        if 'unaugmented' in stype or 'poetic' in stype: pen += 1
        out.append((lem, pos, feats, stype, pen, hwd[2] if hwd else '', field.split(',')[0], field))
    return out
if __name__ == '__main__':
    forms = open(W + '/forms.txt').read().split('\n')
    MS = parse_out(W + '/morph.out'); MN = parse_out(W + '/morph_n.out'); MC = parse_out(W + '/morph_caps.out')
    MV = parse_out(W + '/morph_v.out') if os.path.exists(W + '/morph_v.out') else {}
    VBY = collections.defaultdict(list)
    for vb, lst in (json.load(open(W + '/var_map.json')).items() if os.path.exists(W + '/var_map.json') else []):
        for f0, rule in lst: VBY[f0].append((vb, rule))
    # TAGNT form -> lemma/morph
    TAG = collections.defaultdict(collections.Counter); TAGM = collections.defaultdict(collections.Counter)
    for f in ('mj.txt', 'ar.txt'):
        for l in open('/workspace/src/tagnt/' + f, encoding='utf-8'):
            if not re.match(r'[0-9A-Z][0-9A-Za-z]{2}\.\d+\.\d+#', l): continue
            c = l.rstrip('\n').split('\t')
            if len(c) < 5: continue
            fm = lower_form(c[1].split(' (')[0].strip()); lem = c[4].split('=')[0].strip(); mc = c[3].split('=')[-1]
            if fm and lem: TAG[fm][lem] += 1; TAGM[(fm, lem)][mc] += 1
    json.dump({'TAG': {k: dict(v) for k, v in TAG.items()}, 'TAGM': {k[0] + '\t' + k[1]: dict(v) for k, v in TAGM.items()}}, open(W + '/tagnt_forms.json', 'w'), ensure_ascii=False)
    out = {}; stat = collections.Counter()
    caps = {}
    for b in open(W + '/caps.beta').read().split('\n'):
        if b: caps[b] = MC.get(b, [])
    for f in forms:
        if not f: continue
        b = to_beta(f)
        an = analyses(MS.get(b, [])); ac = analyses(caps.get(to_beta_cap(f), []))
        src = 'M'
        if not an and MN.get(b):
            an = [a for a in analyses(MN[b]) if strip_marks(from_beta(a[6])).replace('ς','σ') == strip_marks(f).replace('ς','σ')]
            src = 'N'
        if not an and VBY.get(f):                 # spelling-variant retry (prep_variants.py)
            for vb, rule in VBY[f]:
                vf = strip_marks(from_beta(vb)).replace('ς', 'σ'); got = []
                for a in analyses(MV.get(vb, [])):
                    if ',' in a[7] and strip_marks(from_beta(a[6])).replace('ς', 'σ') != vf: continue   # field 'form,lemma': the form must match; a bare lemma field means the input matched as given
                    ft = a[2]
                    if rule == 'pl3' and '3rd pl' not in ft: continue
                    if rule == 'verb' and a[1] not in ('V', 'P'): continue
                    if rule == 'imp_pl':
                        if 'imperat' not in ft or '3rd sg' not in ft: continue
                        ft = ft.replace('3rd sg', '3rd pl')
                    got.append((a[0], a[1], ft) + tuple(a[3:]))
                if got: an = got; src = 'V'; break
        if an or ac:
            out[f] = {'src': src, 'a': [[a[0], a[1], a[2], a[3], a[4], a[5]] for a in an], 'ac': [[a[0], a[1], a[2], a[3], a[4], a[5]] for a in ac],
                      'tag': dict(TAG.get(f, {})), 'tagm': {l: TAGM[(f, l)].most_common(1)[0][0] for l in TAG.get(f, {})}}
            stat[src] += 1; continue
        if f in TAG:
            lem, n = TAG[f].most_common(1)[0]
            out[f] = {'src': 'T', 'tagnt': [lem, TAGM[(f, lem)].most_common(1)[0][0]]}; stat['T'] += 1; continue
        h = HW.get(norm(f), [])
        if len({e[1] for e in h}) == 1:
            out[f] = {'src': 'H', 'hw': [h[0][1], h[0][2]]}; stat['H'] += 1; continue
        stat['none'] += 1
    json.dump(out, open(W + '/analysis_raw.json', 'w'), ensure_ascii=False)
    json.dump({k: v for k, v in HW.items()}, open(W + '/headwords.json', 'w'), ensure_ascii=False)
    json.dump(TB, open(W + '/tbesg.json', 'w'), ensure_ascii=False)
    print('forms by route', dict(stat))

#!/usr/bin/env python3
"""Group TAGNT's split NT lemmas under one dictionary headword (NT words only; the LXX is not changed). Idempotent; run in site/ after build_nt.py,
then run nt_counts.py. The word's own form and grammar tag are kept; only the headword (lexicon id) changes.
Writes ../lemma_map_review.tsv (source lemma, target headword, reason, count) incl. proposals NOT applied."""
import json, os, collections, unicodedata
D = 'data'; N = lambda s: unicodedata.normalize('NFC', s)
L = json.load(open(os.path.join(D, 'lexicon.json'))); M = json.load(open(os.path.join(D, 'morph.json')))
def lid(lemma, strong=None):
    c = [k for k, v in L.items() if N(v[0]) == N(lemma) and (strong is None or v[5] == strong)]
    assert c, lemma; return int(min(c, key=int))
SUPP = 'suppletive: another tense stem of the same verb; dictionaries list it under '
VAR = 'spelling variant of the same word; the LXX lexicon already uses '
RULES = [  # (source lemma, strong or None, target lemma, reason, condition on morph code or None)
    ('ἔπω', 'G2036', 'λέγω', SUPP + 'λέγω (εἶπον aorist)', None),
    ('ἔπω', 'G2046', 'λέγω', SUPP + 'λέγω (ἐρῶ future, ἐρρέθη passive)', None),
    ('εἴδω', None, 'ὁράω', SUPP + 'ὁράω (εἶδον, aorist "saw"); only aorist forms', lambda c: c.startswith('V.A')),
    ('εἴδω', None, 'οἶδα', 'perfect with present meaning "know"; dictionaries (BDAG, Abbott-Smith, LSJ) give it its own headword οἶδα; perfect/pluperfect forms only', lambda c: c[:3] in ('V.X', 'V.Y')),
    ('ὁράω', 'G3700', 'ὁράω', 'duplicate headword: TAGNT files ὄψομαι etc. under a second number (G3700); same word', None),
    ('φαγεῖν', None, 'ἐσθίω', SUPP + 'ἐσθίω (ἔφαγον aorist, φάγομαι future)', None),
    ('οὕτω', None, 'οὕτως', VAR + 'οὕτως', None), ('Μωϋσῆς', None, 'Μωσῆς', VAR + 'Μωσῆς', None), ('Δαυείδ', None, 'Δαυίδ', VAR + 'Δαυίδ', None),
    ('πραΰτης', None, 'πραότης', VAR + 'πραότης', None), ('πραΰς', None, 'πρᾶος', VAR + 'πρᾶος', None), ('ἐμπίμπλημι', None, 'ἐμπίπλημι', VAR + 'ἐμπίπλημι', None),
    ('ἑλκύω', None, 'ἕλκω', VAR + 'ἕλκω (ἑλκύσω etc.)', None), ('Ἰεζαβήλ', None, 'Ἰεζάβελ', VAR + 'Ἰεζάβελ', None), ('ἐχθές', None, 'χθές', VAR + 'χθές', None),
    ('ἐννεός', None, 'ἐνεός', VAR + 'ἐνεός', None), ('ἄρκος', None, 'ἄρκτος', VAR + 'ἄρκτος', None), ('γῆρος', None, 'γῆρας', VAR + 'γῆρας', None),
    ('Χανααναῖος', None, 'Χαναναῖος', VAR + 'Χαναναῖος', None), ('συγγενεύς', None, 'συγγενής', VAR + 'συγγενής', None)]
MID = 'LXX lexicon headword is the active form; NT dictionaries use the middle form'
PROPOSED = [('ἀποκρίνω', 'ἀποκρίνομαι', MID), ('πορεύω', 'πορεύομαι', MID), ('φοβέω', 'φοβέομαι', MID), ('ἀπολλύω', 'ἀπόλλυμι', 'LXX lexicon headword is the late -ύω spelling; dictionaries use ἀπόλλυμι')]
src = {}
for s, st, t, why, cond in RULES:
    for k, v in L.items():
        if N(v[0]) == N(s) and (st is None or v[5] == st) and not (s == t and k == str(lid(t))):
            src.setdefault(int(k), []).append((lid(t), t, why, cond, s))
NFC = [0]; cnt = collections.Counter(); books = [b for b in json.load(open(os.path.join(D, 'books.json'))) if b.get('nt')]
for b in books:
    for c in b['chapters']:
        p = os.path.join(D, b['id'], '%s.json' % c); vs = json.load(open(p)); ch = False
        for v in vs:
            for w in v[1]:
                if w[0] != N(w[0]): w[0] = N(w[0]); ch = True; cnt[('_nfc', '', '')] += 0; NFC[0] += 1   # TAGNT uses oxia accents; NFC = same letters as the LXX text
                for tl, t, why, cond, s in src.get(w[1], []):
                    if cond is None or cond(M[w[2]][0]): cnt[(s, t, why)] += 1; w[1] = tl; ch = True; break
        if ch: json.dump(vs, open(p, 'w'), ensure_ascii=False, separators=(',', ':'))
nt = json.load(open(os.path.join(D, 'ntcounts.json')))
print('forms normalised to NFC:', NFC[0])
cnt = collections.Counter({k: v for k, v in cnt.items() if k[0] != '_nfc'})
if not cnt: print('nothing to remap (already applied); review TSV left unchanged'); raise SystemExit
with open('../lemma_map_review.tsv', 'w') as f:
    f.write('source_lemma\ttarget_headword\treason\tcount\tstatus\n')
    for (s, t, why), n in sorted(cnt.items(), key=lambda x: -x[1]): f.write(f'{s}\t{t}\t{why}\t{n}\tapplied (NT words)\n')
    for s, t, why in PROPOSED: f.write(f'{s}\t{t}\t{why}. Shared with the LXX, so NOT applied: needs a decision\t{nt.get(str(lid(s)), 0)} NT\tproposed only\n')
print('applied mappings this run:', len(cnt), 'words remapped:', sum(cnt.values()))

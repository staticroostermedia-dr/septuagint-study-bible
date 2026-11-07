#!/usr/bin/env python3
"""Measured accuracy figures for the NT layer. Usage: check_nt.py SITE SBLGNT_TEXT_DIR WEB_VPL"""
import json, os, re, sys, unicodedata, difflib, random, collections
S, SB, WEB = sys.argv[1:4]; D = os.path.join(S, 'data')
def n(w): return ''.join(c for c in unicodedata.normalize('NFD', w) if unicodedata.category(c) != 'Mn').lower().replace('ς', 'σ').replace('\u2019', '').replace("'", '').replace('\u1fbd', '').replace('\u02bc', '')
books = [b for b in json.load(open(os.path.join(D, 'books.json'))) if b.get('nt')]
lex = json.load(open(os.path.join(D, 'lexicon.json'))); morph = json.load(open(os.path.join(D, 'morph.json')))
st = collections.Counter(); ours = {}
for b in books:
    for c in b['chapters']:
        for v in json.load(open(os.path.join(D, b['id'], '%s.json' % c))):
            st['verses'] += 1; st['verses_with_greek'] += bool(v[1]); st['verses_with_english'] += bool(v[2])
            for w in v[1]:
                st['words'] += 1; st['with_lemma'] += bool(w[1] and str(w[1]) in lex); st['with_grammar'] += bool(w[2] and morph[w[2]][0])
                st['with_dict_tab'] += 0
            ours['%s %s:%s' % (b['id'], c, v[0])] = [n(w[0]) for w in v[1]]
sb = {}; fmap = {'Matt':'Matt','Mark':'Mark','Luke':'Luke','John':'John','Acts':'Acts','Rom':'Rom','1Cor':'1Cor','2Cor':'2Cor','Gal':'Gal','Eph':'Eph','Phil':'Phil','Col':'Col','1Thess':'1Thess','2Thess':'2Thess','1Tim':'1Tim','2Tim':'2Tim','Titus':'Titus','Phlm':'Phlm','Heb':'Heb','Jas':'Jas','1Pet':'1Pet','2Pet':'2Pet','1John':'1John','2John':'2John','3John':'3John','Jude':'Jude','Rev':'Rev'}
for b in books:
    for line in open(os.path.join(SB, b['id'] + '.txt'), encoding='utf-8'):
        m = re.match(r'^\S+ (\d+):(\d+)\t(.*)$', line.strip())
        if m: sb['%s %s:%s' % (b['id'], m.group(1), m.group(2))] = [n(re.sub(r'[⸀⸁⸂⸃⸄⸅.,;·:\[\]—()“”]', '', w)) for w in m.group(3).split()]
sb = {k: [w for w in v if w] for k, v in sb.items()}
same = 0; sbw = sum(len(v) for v in sb.values()); matched = 0
for k in set(ours) | set(sb):
    a, b = ours.get(k, []), sb.get(k, [])
    if a == b: same += 1
    matched += sum(x.size for x in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks())
st['sblgnt_words'] = sbw; st['verses_identical_to_sblgnt'] = same; st['verse_keys_union'] = len(set(ours) | set(sb)); st['word_matches_with_sblgnt'] = matched
print(json.dumps(st, indent=1))
print('lemma %.2f%%  grammar %.2f%%  verses identical to SBLGNT %.1f%%  words agreeing with SBLGNT %.2f%% of ours' % (100*st['with_lemma']/st['words'], 100*st['with_grammar']/st['words'], 100*same/len(set(ours)|set(sb)), 100*matched/st['words']))
random.seed(7); keys = random.sample(sorted(ours), 6)
for k in keys: print(k, '| ours:', ' '.join(ours[k])[:90], '| SBLGNT:', ' '.join(sb.get(k, []))[:90])

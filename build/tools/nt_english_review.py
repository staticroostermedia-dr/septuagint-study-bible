#!/usr/bin/env python3
"""Apply Greek Maestro's NT English review to the WEB English in data/<NT book>/<ch>.json, so the English follows the NA28 Greek.
Run after build_nt.py (build_nt.py calls it at the end); idempotent. Input: build/nt_english/nt_trim_reviewed.tsv
(columns ref, WEB text, ..., decision, final_english, reviewer_note; final_english = the WHOLE verse after all rows for that verse).
  TRIM / EDIT  -> the verse's English becomes final_english (once per verse; all its TRIM/EDIT rows agree)
  KEEP / NONE  -> no change
  MOVE         -> numbering fixes in MOVES below (Rom 14:24-26 -> 16:25-27; 2 Cor 13:14 -> 13:13 without 'Amen', WEB 13:13 -> end of 13:12;
                  3 John 1:14 tail -> 1:15; Rev 13:1 start -> 12:18 as 'Then he stood on the sand of the sea.' (NA28 ἐστάθη))
  BLANK        -> the 12 WEB-only verses (no NA28 Greek): Drake 2026-11-27, "if it's not in the greek text just take it out". The verse row
                  is removed from the chapter (no Greek, no English, no note, no bare verse number); a BLANK verse that has Greek keeps it
                  and loses only its English. --no-blank skips this.
  HOLD         -> (none left: Greek Maestro closed all 10 on 2026-11-27 as TRIM/EDIT/KEEP) rows inside Mark 16:9-20 / John 7:53-8:11, applied like TRIM/EDIT (Drake 2026-11-27: "If the text is there in the greek
                  that we're using, then we should put the english and we don't need to bracket anything"); --no-hold skips them.
OVERRIDES (build/nt_english/overrides.tsv: ref, action append|replace, text, note) is applied last, e.g. the English for the
Mark 16:8 shorter ending, which is in the app's Greek but not in the WEB.
A verse is only changed when its English is still the WEB text the reviewer saw (or already the result); anything else is reported, not touched.
PUNCT holds the punctuation/quote fixes made after the review (Luke 20:30-31, Acts 15:17-18)."""
import csv, json, os, re, sys, collections
SITE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.join(SITE, 'data'); TSV = os.path.join(SITE, 'build', 'nt_english', 'nt_trim_reviewed.tsv')
BOOKS = [b for b in json.load(open(os.path.join(D, 'books.json'))) if b.get('nt')]
BYNAME = {b['name']: b['id'] for b in BOOKS}
APPLY = {'TRIM', 'EDIT'} | (set() if '--no-blank' in sys.argv else {'BLANK'}) | (set() if '--no-hold' in sys.argv else {'HOLD'})
def parse(ref):
    m = re.fullmatch(r'(.+) (\d+):(\w+)', ref); return BYNAME[m.group(1)], m.group(2), m.group(3)
CH = {}
def chap(b, c):
    if (b, c) not in CH: CH[(b, c)] = json.load(open(os.path.join(D, b, f'{c}.json'), encoding='utf-8'))
    return CH[(b, c)]
def row(b, c, v):
    return next((x for x in chap(b, c) if x[0] == v), None)
st = collections.Counter(); problems = []
PUNCTED = {}   # filled from PUNCT below; a verse already carrying its punctuation fix counts as applied
def setv(b, c, v, old, new, why):
    x = row(b, c, v)
    if x is None: problems.append(f'{b} {c}:{v}: verse not found ({why})'); return
    if x[2] == new or (why in ('TRIM', 'EDIT') and x[2] in PUNCTED.get((b, c, v), ())): st['already'] += 1; return
    if old is not None and x[2] != old: problems.append(f'{b} {c}:{v}: English is not the reviewed WEB text, left as is ({why}): {x[2][:80]!r}'); return
    x[2] = new; st[why] += 1
# ---- punctuation / quote fixes on verses the review joined across a verse break ----
PUNCT = [
    # NA28 Luke 20:30-31 καὶ ὁ δεύτερος καὶ ὁ τρίτος ἔλαβεν αὐτήν: one sentence across the break
    ('Luke', '20', '30', 'The second,', 'The second'),
    ('Luke', '20', '31', 'The third took her, and likewise the seven all left no children, and died.', 'and the third took her, and likewise the seven all left no children, and died.'),
    # Acts 15:17-18 ποιῶν ταῦτα γνωστὰ ἀπ᾽ αἰῶνος: the quotation (opened ‘ at v.16) now closes at the end of v.18
    ('Acts', '15', '17', 'that the rest of men may seek after the Lord: all the Gentiles who are called by my name, says the Lord, who does these things.’',
     'that the rest of men may seek after the Lord: all the Gentiles who are called by my name, says the Lord, who does these things'),
    ('Acts', '15', '18', 'known from eternity.', 'known from eternity.’'),
]
for b, c, v, old, new in PUNCT: PUNCTED.setdefault((b, c, v), set()).add(new)
rows = list(csv.DictReader(open(TSV, encoding='utf-8'), delimiter='\t'))
per = collections.OrderedDict()
for r in rows: per.setdefault(r['ref'], []).append(r)
for ref, rs in per.items():
    ds = {r['decision'] for r in rs}
    app = [r for r in rs if r['decision'] in APPLY]
    if not app: continue
    finals = {r['final_english'] for r in app}
    if len(finals) != 1: problems.append(f'{ref}: rows disagree on final_english, skipped'); continue
    dec = 'EDIT' if 'EDIT' in ds else sorted(ds & APPLY)[0]
    if dec != 'BLANK' and not any(r['final_english'].strip() for r in app): problems.append(f'{ref}: {dec} row has no final_english, English left as is'); continue
    b, c, v = parse(ref)
    new = finals.pop().strip()
    if dec == 'BLANK':
        x = row(b, c, v)
        if x is None: st['already'] += 1; continue
        if x[2] != rs[0]['WEB text'] and x[2]: problems.append(f'{ref}: BLANK skipped, English is not the reviewed WEB text'); continue
        if not x[1]: chap(b, c).remove(x); st['BLANK_rows_removed'] += 1
        else: x[2] = ''; del x[3:]; st['BLANK_english_removed'] += 1
        continue
    setv(b, c, v, rs[0]['WEB text'], new, dec)
# ---- MOVE: verse-numbering fixes (WEB numbering -> NA28 numbering) ----
def take(b, c, v):
    x = row(b, c, v); return x[2] if x else None
def drop(b, c, v):   # remove a WEB-only row (no Greek) once its English has moved
    x = row(b, c, v)
    if x is not None and not x[1]: chap(b, c).remove(x); st['MOVE_rows_removed'] += 1
for src, dst in (('14:24', '16:25'), ('14:25', '16:26'), ('14:26', '16:27')):
    (sc, sv), (dc, dv) = src.split(':'), dst.split(':')
    e = take('Rom', sc, sv)
    if e is not None and row('Rom', sc, sv) is not None and not row('Rom', sc, sv)[1]:
        setv('Rom', dc, dv, '', e, 'MOVE'); drop('Rom', sc, sv)
e14 = take('2Cor', '13', '14')
if e14 is not None and not row('2Cor', '13', '14')[1]:
    saints = take('2Cor', '13', '13')
    setv('2Cor', '13', '12', 'Greet one another with a holy kiss.', 'Greet one another with a holy kiss. ' + saints, 'MOVE')
    setv('2Cor', '13', '13', saints, re.sub(r'\s*Amen\.$', '', e14), 'MOVE'); drop('2Cor', '13', '14')
t = take('3John', '1', '14'); TAIL = ' Peace be to you. The friends greet you. Greet the friends by name.'
if t and t.endswith(TAIL) and not take('3John', '1', '15'):
    setv('3John', '1', '14', t, t[:-len(TAIL)], 'MOVE'); setv('3John', '1', '15', '', TAIL.strip(), 'MOVE')
r1 = take('Rev', '13', '1'); HEAD = 'Then I stood on the sand of the sea. '
if r1 and r1.startswith(HEAD) and not take('Rev', '12', '18'):
    setv('Rev', '13', '1', r1, r1[len(HEAD):], 'MOVE'); setv('Rev', '12', '18', '', 'Then he stood on the sand of the sea.', 'MOVE')
for b, c, v, old, new in PUNCT: setv(b, c, v, old, new, 'PUNCT')
# ---- hand-written English for Greek the WEB does not translate ----
OV = os.path.join(SITE, 'build', 'nt_english', 'overrides.tsv')
if os.path.exists(OV):
    for o in csv.DictReader(open(OV, encoding='utf-8'), delimiter='\t'):
        b, c, v = parse(o['ref']); x = row(b, c, v); txt = o['text'].strip()
        if x is None: problems.append(f"{o['ref']}: override target not found"); continue
        if not txt: problems.append(f"{o['ref']}: override has no text yet (placeholder)"); continue
        if o['action'] == 'append':
            if x[2].endswith(txt): st['already'] += 1
            else: x[2] = (x[2].rstrip() + ' ' + txt).strip(); st['OVERRIDE'] += 1
        elif o['action'] == 'replace':
            if x[2] == txt: st['already'] += 1
            else: x[2] = txt; st['OVERRIDE'] += 1
# ---- sanity: no NT verse with Greek is left without English except the HOLD/BLANK-pending ones and Greek the WEB lacks ----
for (b, c), vs in CH.items():
    seen = set()
    for x in vs:
        if x[0] in seen: problems.append(f'{b} {c}:{x[0]}: duplicate verse row')
        seen.add(x[0])
        if not x[1] and not x[2]: problems.append(f'{b} {c}:{x[0]}: row with neither Greek nor English')
    json.dump(vs, open(os.path.join(D, b, f'{c}.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(json.dumps(dict(st)), f'verses: {sum(1 for r, rs in per.items() if any(x["decision"] in APPLY for x in rs))} reviewed for change')
for p in problems: print('  !', p)

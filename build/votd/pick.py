#!/usr/bin/env python3
"""Daily Verses list (Gallicantus batch): grow the approved 366 Verse-of-the-Day list to 1,830 verses = 366 days x 5, no repeats.
Day N (leap-year calendar, Jan 1 = 1 ... Dec 31 = 366) shows lines 5N-4 .. 5N of build/votd/verses.tsv; its first verse is the approved verse
for that date (unchanged, same pins: 1 Jan Gen 1:1, 25 Dec Luke 2:14 ...). The other four come from:
  1. 'draft': verses from the earlier hand-made draft list (build/votd/draft.txt) that were not used in the final 366;
  2. 'auto': verses chosen by the rules below, best score first, with per-book quotas so they spread across the Bible.
Rules for 'auto' (a verse must pass all):
  - Greek and English present; English not hidden, joined, moved or marked 'Greek differs' (alignment status), no '[Br.' marker;
  - English 8-45 words, starts with a capital letter, ends a sentence (. ! ?), balanced brackets, at most one unmatched quote mark
    (the WEB opens or closes a speech inside a verse);
  - does not begin with a word that ties it to the verse before (And, Then, So, Therefore, He, They, This, These, It ...);
    'For' and 'But' are allowed only in verses with 3+ theme words (e.g. 'But the fruit of the Spirit is love, joy, peace ...');
  - at least 2 theme words (1 in the New Testament);
  - at most one personal or place name (other than God, Lord, Christ, Jesus, Israel, Sion/Zion, Jerusalem ...), no numbers or measures;
  - no words from a short list of narrative/ritual/violent terms (slew, smote, cubits, shekels, burnt-offering, harlot ...);
  - not next to another chosen verse in the same chapter.
  Score = theme words (God, Lord, love, mercy, righteous, wisdom, heart, hope, peace, praise, light, life, truth, trust, salvation, ...)
  + half a point per 'warm' word (love, mercy, grace, peace, hope, joy, praise, bless, trust, light, life ...) + 1.5 for 12-30 words
  + 1 for direct speech to God or the reader (O, I, you/thou, blessed, let us ...) - 0.75 per heavy word (wrath, death, evil, curse,
  sword, fire, shame ...) - 1.5 when it reads as narrative (said, came, went, answered, sent ...).
  Quotas: Septuagint 48%, Apocrypha 11%, New Testament 41% (the approved list's shares); inside a section each book's share grows with the
  square root of its number of passing verses, capped at 18% of the section, so the Psalms, Proverbs and Sirach do not take over.
Order: each day's four extra verses are taken round-robin from the three sections (LXX, NT, LXX/Apocrypha, NT) and from different books
where possible, in a fixed seeded order, so every date always gets the same five verses.
Usage: python3 build/votd/pick.py  (writes build/votd/verses.tsv; then python3 build/tools/build_votd.py)"""
import collections, json, math, os, random, re
SITE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); D = os.path.join(SITE, 'data')
HERE = os.path.dirname(os.path.abspath(__file__))
APPROVED = os.path.join(HERE, 'approved366.tsv'); DRAFT = os.path.join(HERE, 'draft.txt')   # approved list (one per date); earlier hand-made draft; DRAFT = '/workspace/lxx-latin/votd/draft.txt'
DAYS, PER = 366, 5
books = json.load(open(D + '/books.json', encoding='utf-8'))
APOC = {'Tob', 'Jdt', '1Macc', '2Macc', '3Macc', '4Macc', 'Wis', 'Sir', 'Bar', 'EpJer', 'Sus', 'Bel', '1Esdr', '4Esdr', 'PrMan'}
def section(b): return 2 if b['nt'] else 1 if b['id'] in APOC else 0
for b in books: b['nt'] = bool(b.get('nt'))
BYID = {b['id']: b for b in books}
def verses(bid, c):
    p = f'{D}/{bid}/{c}.json'
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else []
approved = [l.rstrip('\n').split('\t') for l in open(APPROVED, encoding='utf-8')][1:]
approved = [a for a in approved if a and a[0]]
assert len(approved) == DAYS, len(approved)
used = {a[0] for a in approved}
OPEN = re.compile(r"^(and|but|for|then|so|therefore|wherefore|now|thus|also|moreover|because|that|which|who|whom|whose|when|whenever|while|after|afterward|before|if|or|nor|yet|saying|lest|as|even|again|until|till|since|though|although|neither|nevertheless|notwithstanding|furthermore|likewise|besides|hence|accordingly|he|she|they|him|her|them|his|their|these|this|those|it|its|there|here|such|thereupon|where|whereas|what|how|by this|in this|in that|on this|at that|from that|from this|with these|after these|after this)\b", re.I)
NAMEOK = {'God', 'Lord', 'LORD', 'Christ', 'Jesus', 'Israel', 'Sion', 'Zion', 'Jerusalem', 'Jacob', 'Spirit', 'Holy', 'Father', 'Son', 'Most', 'High', 'Almighty', 'I', 'O', 'Amen', 'Heaven', 'Lord’s', 'God’s', 'Christ’s'}
BADW = re.compile(r"\b(slew|slay|slain|smote|smite|smitten|killed|kill|cubits?|shekels?|talents?|burnt[- ]offerings?|whole[- ]burnt|harlot|whore|whoredom|fornication|adulter\w*|uncircumcised|circumcis\w*|foreskin|dung|bullocks?|rams?|he-goats?|goats?|heifer|calves|fat of|entrails|kidneys|blood|corpse|carcase|leprosy|leper|issue|unclean|eunuch\w*|concubine|virgins?|naked|nakedness|wine-press|tribe of|sons of \w+|daughters of \w+|captain|chariots?|horsemen|army|armies|besieged|siege|camp|tabernacle of witness|ark|altar|priests?|levites?|sabbaths?|feast of|month|months|year|years|day of the month|thousand|hundred|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|eight|nine|ten|eleven|twelve|four|five|six|tenth|fourth|fifth|sixth|seventh|eighth|ninth|beat|beaten|scourge\w*|stone him|crucify|devils?|demons?|swine|asses?|camels?|sheep-gate|spake unto|said unto|answered and said|wrote|letter|epistle|greet|salute|saluteth|cast lots|lots|beast|beasts|drunk\w*|stupor|stupified|fatal\w*|wounded|darnel|weeds|vomit\w*|whip|prison|chains|feasts|assembl\w*|householder|hill country|immorality|sexual|servants, obey|slaves?)\b", re.I)
NEG = re.compile(r"\b(wrath|anger|angry|destroy\w*|death|die|died|dead|evil|wicked|ungodly|sinners|darkness|curse\w*|cursed|enemies|enemy|perish\w*|woe|desolat\w*|abomination\w*|famine|pestilence|sword|fire|burn\w*|lament\w*|weep\w*|shame|ashamed)\b", re.I)
NARR = re.compile(r"\b(said|says|saith|came|went|answered|told|spoke|spake|arose|sent|brought|heard this|took)\b", re.I)
WARM = re.compile(r"\b(love[sd]?|loving|mercy|mercies|merciful|grace|gracious|peace|hope|joy|rejoice\w*|praise[sd]?|bless\w*|trust\w*|salvation|light|life|righteous\w*|faithful\w*|refuge|comfort\w*|everlasting|eternal|wisdom|truth|kindness|goodness|thanks)\b", re.I)
THEME = re.compile(r"\b(god|lord|love[sd]?|loving|mercy|mercies|merciful|compassion\w*|righteous\w*|just|justice|wisdom|wise|understanding|knowledge|heart|soul|faith|faithful\w*|hope|peace|praise[sd]?|bless\w*|salvation|save[sd]?|saviour|savior|deliver\w*|redeem\w*|redemption|glory|glorif\w*|grace|gracious|truth|true|light|life|live|living|joy|joyful|rejoice\w*|glad|gladness|trust\w*|fear|holy|holiness|forgive\w*|eternal|everlasting|for ever|strength|strong|refuge|rock|shield|comfort\w*|word|spirit|kingdom|pray\w*|humble|humility|meek|poor|needy|help|helper|shepherd|beloved|thanks|thanksgiving|sing|song|good|goodness|kind|kindness|patien\w*|gentle|pure|clean heart|repent\w*|sin|sins|iniquit\w*|seek|wait|walk|way|ways|path|commandments?|law|teach|learn|counsel|instruction|discipline|heal\w*|rest|bread of life|children|neighbour|neighbor|brother|friend|gift|grace)\b", re.I)
SPEECH = re.compile(r"^(o |i |my |thou|you|ye |blessed|happy|let us|let |the lord|lord|god|praise|give thanks|sing|trust|seek|fear|hear|come|behold|whoever|whosoever|everyone|every one|all |the fear|wisdom|a wise|a righteous|the righteous|the wise|better|do not|be not|love|rejoice)", re.I)
def names(en):
    ws = re.findall(r"(?<![.!?;:“‘\"(] )(?<!^)\b([A-Z][a-z’']+)", en)
    return [w for w in ws if w not in NAMEOK]
def passes(x, bid):
    en = (x[2] or '').strip(); es = x[3] if len(x) > 3 else None
    if not x[1] or not en: return None
    if es and (es.get('s') in ('h', 'j', 'd', 'm', 'r', 'g0') or es.get('gd')): return None
    if '[' in en or re.search(r'\d', en): return None
    n = len(en.split())
    if not 8 <= n <= 45 or not en[0].isupper() or not re.search(r"[.!?][’”\"']*\)?$", en): return None
    if en.count('(') != en.count(')') or abs(en.count('“') - en.count('”')) > 1: return None
    th = len(set(m.lower() for m in THEME.findall(en)))
    op = OPEN.match(en.lstrip('“‘"\'('))
    if op and not (op.group(1).lower() in ('for', 'but') and th >= 3): return None
    if BADW.search(en) or len(names(en)) > 1: return None
    if th < (1 if BYID[bid]['nt'] else 2): return None
    if re.match(r'^(only|fear came|fear took|one of|however)\b', en, re.I) or re.match(r'^[A-Z][a-z]{1,6}\. ', en): return None   # Lamentations acrostic letters (Chaph. ...)
    warm = len(set(m.lower() for m in WARM.findall(en)))
    return th + 0.5 * warm + (1.5 if 12 <= n <= 30 else 0) + (1 if SPEECH.match(en.lstrip('“‘"\'(')) else 0) - 0.75 * len(NEG.findall(en)) - 1.5 * bool(NARR.search(en))
# 1. draft extras
draft = []
for l in open(DRAFT, encoding='utf-8'):
    p = l.rstrip('\n').split('|')
    if p and p[0].strip() and p[0].strip() not in used: draft.append((p[0].strip(), (p[1].strip() if len(p) > 1 else '')))
pool = collections.defaultdict(list)   # section -> [(ref, bid, c, v, score, reason)]
chosen = {}   # ref -> (section, bid, reason)
for ref, why in draft:
    m = re.fullmatch(r'(\S+) (\d+):(\w+)', ref)
    if not m or m.group(1) not in BYID: continue
    bid, c, v = m.groups(); x = {str(y[0]): y for y in verses(bid, c)}.get(v)
    if not x or not x[1] or not x[2]: continue
    es = x[3] if len(x) > 3 else None
    if es and es.get('s') in ('h', 'j'): continue
    chosen[ref] = (section(BYID[bid]), bid, 'draft: ' + why)
# 2. auto candidates
cand = collections.defaultdict(lambda: collections.defaultdict(list))
for b in books:
    for c in b['chapters']:
        for x in verses(b['id'], c):
            v = str(x[0]); ref = f"{b['id']} {c}:{v}"
            if ref in used or ref in chosen or not v.isdigit(): continue
            s = passes(x, b['id'])
            if s is not None: cand[section(b)][b['id']].append((s, int(str(c)) if str(c).isdigit() else 0, int(v), ref, x[2]))
need = DAYS * (PER - 1)
share = [0.48, 0.11, 0.41]
have = collections.Counter(s for s, _, _ in chosen.values())
rng = random.Random(20261121)
stats = {}
for sec in range(3):
    want = round(need * share[sec]) - have[sec] if sec < 2 else need - len(chosen)
    bk = cand[sec]; w = {b: math.sqrt(len(xs)) for b, xs in bk.items()}; tot = sum(w.values()) or 1
    quota = {b: min(len(bk[b]), max(1, round(want * w[b] / tot)), int(0.18 * want) + 1) for b in bk}
    # adjust to hit 'want' exactly: add to books with spare candidates, largest weight first
    order = sorted(bk, key=lambda b: -w[b])
    for _ in range(10000):
        if sum(quota.values()) >= want: break
        grow = [b for b in order if quota[b] < len(bk[b]) and quota[b] < int(0.25 * want)]
        if not grow: break
        for b in grow:
            if sum(quota.values()) >= want: break
            quota[b] += 1
    for _ in range(10000):
        if sum(quota.values()) <= want: break
        shrink = [b for b in order if quota[b] > 1]
        if not shrink: break
        for b in shrink:
            if sum(quota.values()) <= want: break
            quota[b] -= 1
    picked = 0
    for b, xs in bk.items():
        xs.sort(key=lambda t: (-t[0], t[1], t[2])); taken = set()
        for s, c, v, ref, en in xs:
            if sum(1 for k in taken if k[0] == c and abs(k[1] - v) <= 1): continue
            if len([k for k in taken]) >= quota[b]: break
            taken.add((c, v)); chosen[ref] = (sec, b, f'auto: score {s:g}'); picked += 1
    # top-up: quotas can fall short (neighbour rule, small books): take the best remaining verses of the section, max 25% per book
    left = sorted(((t, b) for b, xs in bk.items() for t in xs if t[3] not in chosen), key=lambda z: (-z[0][0], z[1], z[0][1], z[0][2]))
    cnt = collections.Counter(b for r, (s2, b, _) in chosen.items() if s2 == sec)
    for (s, c, v, ref, en), b in left:
        if picked >= want: break
        if cnt[b] >= 0.25 * want: continue
        if any(r.split()[0] == b and r.split()[1].split(':')[0] == str(c) and abs(int(r.split(':')[1]) - v) <= 1 for r in chosen if r.startswith(b + ' ')): continue
        chosen[ref] = (sec, b, f'auto: score {s:g}'); picked += 1; cnt[b] += 1
    stats[sec] = {'wanted': want, 'picked': picked, 'books': len(bk), 'candidates': sum(len(x) for x in bk.values())}
extra = list(chosen.items())
assert len(extra) >= need, (len(extra), need, stats)
# trim (lowest auto scores first) if over
if len(extra) > need:
    def sc(it): r = it[1][2]; return float(r.split()[-1]) if r.startswith('auto') else 99
    extra.sort(key=sc); extra = extra[len(extra) - need:]
rng.shuffle(extra)
by = collections.defaultdict(list)
for ref, (sec, b, why) in extra: by[sec].append((ref, b, why))
pattern = [0, 2, 1, 2]   # LXX, NT, Apocrypha (or LXX when used up), NT
out = [('ref', 'reason', 'source')]
for d in range(DAYS):
    a = approved[d]; out.append((a[0], a[1], 'approved')); dayb = {a[0].split()[0]}
    for slot in pattern:
        order = [slot] + [s for s in (0, 2, 1) if s != slot]
        for sec in order:
            if by[sec]:
                i = next((k for k, it in enumerate(by[sec]) if it[1] not in dayb), 0)
                ref, b, why = by[sec].pop(i); dayb.add(b); out.append((ref, why, 'draft' if why.startswith('draft') else 'auto')); break
assert len(out) - 1 == DAYS * PER and len({r[0] for r in out[1:]}) == DAYS * PER
with open(os.path.join(HERE, 'verses.tsv'), 'w', encoding='utf-8') as f:
    for r in out: f.write('\t'.join(r) + '\n')
src = collections.Counter(r[2] for r in out[1:]); secn = collections.Counter(section(BYID[r[0].split()[0]]) for r in out[1:])
print(json.dumps({'rows': len(out) - 1, 'by_source': src, 'by_section(LXX,Apoc,NT)': [secn[0], secn[1], secn[2]], 'books_used': len({r[0].split()[0] for r in out[1:]}), 'auto': stats}, indent=1))

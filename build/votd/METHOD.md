# Daily Verses: how the 1,830 verses were picked

For Greek Maestro's review. The script is `build/votd/pick.py` and the output is `build/votd/verses.tsv`, with columns ref, reason and source (approved / draft / auto).

```
Daily Verses list (Gallicantus batch): grow the approved 366 Verse-of-the-Day list to 1,830 verses = 366 days x 5, no repeats.
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
Usage: python3 build/votd/pick.py  (writes build/votd/verses.tsv; then python3 build/tools/build_votd.py)
```

## Result
- Total rows: 1,830 (plus a header line); by source: approved 366, auto 1361, draft 103
- By section: LXX 881, Apocrypha 198, NT 751. There are 78 books; Psalms gives the most verses (156).
- Review suggestion: the 'auto' rows are machine-picked. Please skim them and swap out any that read poorly out of context. Then rerun `python3 build/votd/pick.py` with those verses added to an exclude list, or edit verses.tsv directly and run `python3 build/tools/build_votd.py`.

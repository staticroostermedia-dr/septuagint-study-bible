# NT trim review: Greek Maestro's decisions on Mason's candidate list

**Files**
- Input: `nt_trim_candidates.tsv`, with 632 rows from Mason.
- Output: `nt_trim_reviewed.tsv`, with 633 rows. That's the original 632 plus 1 row I added, 2 Peter 3:18. Three columns are new: `decision`, `final_english` and `reviewer_note`.
- Scratch work and the per-row decision files are in `nt_trim_review/`. `build.py` rebuilds the TSV from `dec1–6.txt`.

**Method**
- I checked every row against the TAGNT word list: NA28 versus TR/Byz words, and their glosses.
- Where the two sources disagreed, I checked the app's own Greek tokens in `site/data/<book>/<ch>.json`.
- When a verse has several rows, `final_english` gives the whole verse after all of its rows are applied. Apply it once per verse.
- Nothing was applied, built, or pushed.

## Counts

| Decision | Rows | Meaning |
|---|---|---|
| TRIM | 182 | Mason's proposed text is correct as it stands |
| EDIT | 386 | The cut is right, but the English needed fixing, or the tool cut the wrong words. Use `final_english` |
| KEEP | 23 | The words do translate NA28 Greek (or English needs them), so no change |
| NONE | 16 | The "not in WEB" rows where the WEB really has nothing to cut |
| BLANK | 12 | WEB-only whole verses: blank the English. Proposed note: "Not in the NA28 Greek text." Drake still needs to confirm |
| MOVE | 4 | Numbering mismatches; target refs are below |
| HOLD | 10 | Inside Mark 16:9–20 or John 7:53–8:11; waiting on Drake's bracket decision |

**Why EDIT is so common**
- In most EDIT rows the cut left broken English, for example "Get Satan!", "to son", "sinners to." or "Said to him".
- Names were replaced with "he" or "him" where NA28 has no named subject. That covers about 60 "Jesus/Saul/Paul/the Lord" rows.

**Three kinds of tool error**
- **Wrong words cut: at least 25 rows.** The tool removed words that ARE in NA28, while the TR-only words stayed. Examples:
  - Matt 6:15: it cut the second "trespasses" (NA28 has it) instead of the first.
  - Matt 19:16: it cut "good thing" instead of "Good teacher".
  - Matt 26:42: it cut "drink".
  - Mark 9:23, 9:38, 12:33 and 13:18.
  - Luke 4:41 and 23:38 ("over him").
  - John 6:22 and 12:1.
  - Acts 2:7 and 5:24.
  - Rom 11:6 and 16:18.
  - 1 Cor 11:24 ("which is for you" is NA28) and 11:27.
  - 2 Thess 2:4, 1 Tim 3:3, Heb 10:30 and 13:21.
  - Rev 16:9 and 19:12.
- **"Not in WEB" rows that are in the WEB: 18 rows.** Mason marked them "nothing to trim":
  - 7 have TR wording the WEB does translate: Matt 19:17, Matt 28:9a, Mark 8:26b, Mark 14:27 ("because of me tonight"), Luke 9:55b ("You don't know what kind of spirit you are"), Rom 14:6b and 1 Pet 4:14b.
  - 11 are closing "Amen"s that NA28 lacks: 1 Cor 16:24, Eph 6:24, Phil 4:23, Col 4:18, 1 Thess 5:28, 2 Thess 3:18, 1 Tim 6:21, 2 Tim 4:22, Titus 3:15, Phlm 25 and Heb 13:25.
- **Missed rows: 2 Peter 3:18 (added).** A scan of every NT "Amen" found this final "Amen", which has no NA28 basis. Revelation 22:21 "the saints" was also missing from the tool's list; the app's Greek is just μετὰ πάντων. It's covered in that row's EDIT.

## Numbering mismatches (MOVE)

| WEB now | Move English to (NA28) | Note |
|---|---|---|
| Rom 14:24 | Rom 16:25 | Then remove WEB 14:24–26, since NA28 has no such verses |
| Rom 14:25 | Rom 16:26 | |
| Rom 14:26 | Rom 16:27 | Its "Amen" is in NA28 |
| 2 Cor 13:14 | 2 Cor 13:13 | Drop the final "Amen". Also append WEB 13:13 "All the saints greet you." to the end of 13:12 |
| 3 John 1:14 (end) | 3 John 1:15 | "Peace be to you. The friends greet you. Greet the friends by name." |
| Rev 13:1 (start) | Rev 12:18 | NA28 reads ἐστάθη, "he (the dragon) stood". So the moved English must read "Then he stood on the sand of the sea.", not "I stood" (the TR reading) |

## Notable removals (for Drake)

| Passage | English removed | Why |
|---|---|---|
| Matt 5:44 | "bless those who curse you, do good to those who hate you … mistreat you and" | Not in NA28; TR/Byz borrowed it from Luke 6:27–28 |
| Matt 6:13 | "For yours is the Kingdom, the power, and the glory forever. Amen." | The doxology was added in later manuscripts |
| Matt 19:9 | "and he who marries her when she is divorced commits adultery" | Borrowed from Matt 5:32; "commits adultery" (μοιχᾶται) stays |
| Matt 19:17 | "Why do you call me good? No one is good but one, that is, God" | NA28 reads "Why do you ask me about what is good? There is one who is good." The WEB follows the TR here |
| Matt 20:16 | "For many are called, but few are chosen." | Borrowed from Matt 22:14 |
| Matt 20:22–23 | "and be baptized with the baptism that I am baptized with" | Borrowed from Mark 10:38–39 |
| Matt 25:13 | "in which the Son of Man is coming" | Not in NA28 |
| Mark 6:11 | "Assuredly … more tolerable for Sodom and Gomorrah … than for that city!" | Borrowed from Matt 10:15 |
| Mark 9:29 | "and fasting" | Not in NA28 (same in Matt 17:21, a whole verse) |
| Mark 9:44, 46 + 9:45, 49 | "where their worm doesn't die…", "into the fire that will never be quenched", "every sacrifice will be seasoned with salt" | NA28 has the worm line only once (v.48) |
| Luke 4:4 | "but by every word of God" | Borrowed from Matt 4:4 |
| Luke 4:8 | "Get behind me, Satan!" | Borrowed from Matt 4:10. Matt 4:10 itself only loses "behind me", so it reads "Go away, Satan!" |
| Luke 9:54–56 | "just as Elijah did", "You don't know what kind of spirit you are", "For the Son of Man didn't come to destroy men's lives…" | Not in NA28 |
| Luke 11:2–4 | "Our … in heaven", "May your will be done…", "but deliver us from the evil one" | Luke's shorter prayer: "Father, may your name be kept holy. May your Kingdom come." |
| Luke 23:38 | "written … in letters of Greek, Latin, and Hebrew" | "over him" stays (ἐπ᾽ αὐτῷ) |
| John 5:3–4 | "waiting for the moving of the water" + v.4 (the angel) | Not in NA28 |
| John 6:69 | "the Christ, the Son of the living God" becomes "the Holy One of God" | NA28 ὁ ἅγιος τοῦ θεοῦ |
| Acts 15:24 | "saying, 'You must be circumcised and keep the law,'" | Not in NA28 |
| Acts 28:16 | "the centurion delivered the prisoners to the captain of the guard" | Not in NA28 |
| Rom 8:1 | "who don't walk according to the flesh, but according to the Spirit" | Borrowed from 8:4 |
| Rom 11:6 | "But if it is of works, it is no longer grace; otherwise work is no longer work." | Not in NA28 |
| 1 Cor 6:20 | "and in your spirit, which are God's" | Not in NA28 |
| 1 Cor 11:24 | "Take, eat" and "broken" | NA28 reads "This is my body, which is for you" |
| 1 John 4:3 | "Christ has come in the flesh" | NA28 reads "every spirit who doesn't confess Jesus" |
| 12 whole verses | Matt 17:21, 18:11, 23:14; Mark 7:16, 9:44, 9:46, 11:26, 15:28; Luke 23:17; John 5:4; Acts 28:29; Rom 16:24 | BLANK, Drake to confirm |

## Rows I'm unsure of (wording choices; the Greek basis is clear)

- **Luke 20:30 (rows 269/270).** NA28 v.30 is only "and the second". I set it to "The second,". Verse 31 might read better as "and the third took her…".
- **John 10:13 (339).** It now starts lowercase ("because he is a hired hand…"), continuing v.12. I changed v.12's final period to a comma.
- **Acts 15:18 (398).** The verse is now "known from eternity.", completing v.17's quote. The closing quote mark on v.17 should move to v.18.
- **Phil 3:16 (523).** "let's walk by the same." is literal. "let's keep in step with the same" is an alternative.
- **Rewordings, close to NA28 but not WEB's words:**
  - Matt 19:17 (53).
  - Mark 11:8 (160): "others spread branches that they had cut from the fields".
  - Rom 9:28 (447).
  - 1 John 5:13 (594).
  - Luke 24:46 (289).
  - Phlm 12 (556).
  - 2 Tim 2:3 (548).
  - Mark 8:16 (138): "that they had no bread".
- **Mark 2:16 (109/110).** "Why does he eat…?" reads NA28 ὅτι as a question. A statement, "He eats with…!", is also defensible.
- **Luke 5:33 (215).** Now a statement, since NA28 has no "why".
- **Matt 23:19 (74).** "You blind men!"
- **John 7:39 (318).** I kept "given" as an English supply: οὔπω γὰρ ἦν πνεῦμα.
- **KEEP rows where the tool was right that the Greek word is missing, but English needs it:**
  - "if": Matt 7:9, 7:10; Luke 11:12.
  - "hour": Matt 20:6.
  - "subject": Eph 5:22.
  - "body": 1 Cor 15:44.
  - "rain": Jas 5:7.
  - "hand": Rev 1:17; Gal 2:9.
  - "as great as": Rev 21:16.
- **Outside this list:** NA28 has some words that the WEB doesn't translate, for example Jude 25 "through Jesus Christ our Lord … before all time" and Acts 20:4 "son of Pyrrhus". Mason's `units_not_found_in_WEB.tsv` (231 rows) covers these. Adding English is a separate decision.

## Spot-check: the 1,436 unlisted "function-word-only" additions

- **The lowercase group can be skipped.** 1,334 of the 1,436 are TAGNT lowercase "k" (no effect on translation). In a random sample of 30, the lowercase ones were extra articles, δέ/γάρ/καί, or an extra αὐτοῦ/αὐτῷ that the English doesn't show at all, or shows only as "his/him". None changes the meaning.
- **The 102 uppercase (K/O) units sometimes show up as a pronoun or short phrase in the WEB.** Examples:
  - 1 Cor 10:23: "lawful *for me*".
  - Eph 4:6: "in *us* all"; NA28 has "in all".
  - 1 Pet 4:1: "suffered *for us*".
  - 1 John 3:5: "*our* sins".
  - Mark 13:27: "*his* angels".
  - Acts 13:40: "come *on you*".
  - Phlm 25: "*our* Lord". This one is fixed in the reviewed file.
- **Effect and recommendation.** None of these is a big change, but a few (1 Pet 4:1, 1 John 3:5, Eph 4:6) slightly narrow or broaden the sense. I recommend a quick second pass on just those 102, and no work on the 1,334. `nt_trim_review/fw_all.json` lists all 1,436 units.

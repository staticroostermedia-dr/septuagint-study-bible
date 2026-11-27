# Gallicantus Workbook: Unit 1 · Reading John

A standalone, static copy of the Gallicantus Unit 1 workbook (a first unit that teaches beginner New Testament Greek by reading the Gospel of John). It is built on Harper and Weidner’s inductive method. It is a sketch of a unit, not a reproduction of their lessons or their wording.

This folder is plain web files. It does not need the Cursor canvas runtime. Open it in a browser through a simple static server (recommended) or, in many browsers, by opening `index.html` directly (`js/data.js` is embedded so `file://` works).

Lessons 1–50 (the whole Gospel of John, through the final review) and the related ἐστίν lesson (“God is love,” 1 John 4:8 and more) are fully built: Lesson / Charts / Rules / Words / Practice, including option shuffles, matching derangement, tile shuffles, and progress saved in `localStorage`. The unit map lists all fifty John lessons, and all fifty are ready. Doubtful OCR items and places where the app’s NA28 / trimmed WEB differ from an untrimmed English Bible are listed in `NOTES.md`.

## How to run

From this folder:

```bash
python3 -m http.server 8000
```

Then open http://localhost:8000/ in a browser.

Or, from the parent of this folder:

```bash
python3 -m http.server 8000 --directory workbook
```

To run a syntax check without a browser:

```bash
node --check js/engine.js && node --check js/app.js && node --check js/data.js
```

## Adding a lesson (Antigravity or any editor)

1. Edit `data/unit1.json`. Add a new object under `lessons` with the same shape as `"1"`–`"4"` (verses, `passages` with word tokens and glosses, `words`, `patternHeading` / `patternText` / `patternRows`, `rules`, `choices`, `writes`, `rereadGreek` / `rereadEnglish`, optional `chartExtra` and `phrases`, and a `practice` array of about thirteen items). Use `kind: "review"` for the review lessons (X, XX, XXXI, XL, L) if you follow that pattern later.
2. Set the matching row in `unitMap` to `"status": "Ready"`.
3. Add any new lemma/parse rows to `glossParse`.
4. Rebuild the embedded data file so `file://` stays in sync:

```bash
python3 ../scripts/embed_data.py
```

(run from this folder; or `python3 scripts/embed_data.py` from `workbook-export/`).

The app treats every key in `lessons` as a ready lesson and will show it on the unit map and in Charts / Words / Practice. Keep the same quality rules as Lessons 1–4: short beginner rule cards from what Harper actually teaches (flag a point if his note is implicit or the OCR is unclear); shuffle multiple-choice options; derange matching English so no correct pair sits on the same row, and grade by pair id; do not present word tiles in answer order; do not show the target Greek on the same screen as a “which sentence is written correctly?” / apply-the-rule item.

Progress uses the same `localStorage` key as the Cursor Page (`gallicantus.workbook.reading-john.v4`) and the same v4–v8 migration, so a place already saved in the Page will load here in the same browser profile.

## Sources and licences

- **Harper and Weidner.** William Rainey Harper and Revere Franklin Weidner, *An Introductory New Testament Greek Method* (1889; 1916 edition), **public domain**. Scan: [archive.org/details/introductorynewt00harp](https://archive.org/details/introductorynewt00harp). This workbook is built on their inductive path through John; it is not a reprint of their wording.
- **Greek text: STEPBible TAGNT (Tyndale House, CC BY 4.0), following NA28 wording.** The Gospel verses use the STEPBible TAGNT Greek ([Tyndale House](https://github.com/tyndale/STEPBible-Data), Creative Commons Attribution 4.0), following the wording of the Nestle-Aland *Novum Testamentum Graece*, 28th edition, as in the Gallicantus app. This is not Harper’s printed critical text (Westcott-Hort / Tregelles / Tischendorf in Part II of the 1916 book). Lessons 1–10 were first drafted from the SBLGNT text used on the Cursor Page; TAGNT/NA28 and SBLGNT agree at the points those lessons teach, including μονογενὴς θεός at John 1:18, though some spelling details in Lessons 1–10 may still follow the Page (see `NOTES.md`).
- **English lines: World English Bible (public domain), trimmed to the Greek.** English lines are the World English Bible, 2020 stable text, which is in the **public domain** ([eBible.org/web](https://eBible.org/web/)), as already trimmed in the Gallicantus app to match the Greek where a trim has been reviewed. Where a trim is not yet available, the workbook follows the Greek, not TR or untrimmed WEB additions. See `NOTES.md`.
- **Doubtful OCR and text flags.** `NOTES.md` lists Harper OCR items that should be checked against a clear scan, and verse-level differences such as John 1:18, 1:42, and 1:51.

## File list

- `index.html` — page shell
- `css/workbook.css` — layout and typography
- `js/engine.js` — shuffle, scoring, `localStorage`
- `js/app.js` — the workbook UI
- `js/data.js` — embedded copy of the unit data (generated)
- `data/unit1.json` — lesson and practice data (edit this)
- `NOTES.md` — OCR doubts and NA28 / WEB-trim flags

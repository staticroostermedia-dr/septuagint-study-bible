# Septuagint Study Bible: clean-licence preview (branch `clean-license`, not published)

This branch is a local preview of the reader. It is built only from sources whose licences allow a registered company to publish it
free of charge with a donation request. It uses no NC-licensed data and nothing derived from CCAT, CATSS or Rahlfs.

- **Greek:** Brenton's Greek (1851), eBible.org `grcbrent`, public domain.
- **English:** Brenton (1851) and LXX2012, both public domain (eBible.org). They are paired with the Greek by the same reference.
- **Dictionary forms and grammar:** tagged automatically with Morpheus (MPL-2.0, run at build time, not shipped), STEPBible TAGNT forms and
  TBESG/TFLSJ/Dodson headwords. A separate CC BY-SA layer (`data/wk/`) holds Wiktionary links for about 0.2% of the words.
- **Meanings:** Dodson (PD/CC0), STEPBible TBESG/TFLSJ (CC BY 4.0), and 12 hand-written headlines.
- **Brenton's wording:** automatic alignment of the Brenton Greek/English pairs.

Licences and attributions: `NOTICE` and the About page. The site licence (`LICENSE`) still says CC BY-NC-SA 4.0, as on `preview-changes`. That
licence was required only by the Rahlfs/CCAT data, which this branch no longer uses. The owner still has to choose the new licence.

## Rebuild
The scripts are in `build/tools/` (`run_clean.sh`). Inputs: eBible VPL files (grcbrent, eng-Brenton, eng-lxx2012), STEPBible TBESG/TFLSJ/TAGNT,
Dodson, the kaikki.org Ancient Greek dump, and a local Morpheus build (github.com/perseids-tools/morpheus, with the stemlib it ships).
Test: `(cd site && python3 -m http.server 8771) & python3 build/test_site_clean.py`.

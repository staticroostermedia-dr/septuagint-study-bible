#!/bin/sh
# Clean-licence rebuild (branch clean-license). Inputs: eBible grcbrent + eng-Brenton + eng-lxx2012 (PD), STEPBible TBESG/TFLSJ/TAGNT (CC BY 4.0),
# Dodson (PD/CC0), Wiktionary via kaikki.org (CC BY-SA 4.0, separate layers), Morpheus (MPL-2.0, run locally; /workspace/morpheus-src).
set -e
# Morpheus build note: gkdict.a must contain only dictio.o derivio.o compnoun.o (a stray xderivio.o broke all reduplicated perfects).
cd "$(dirname "$0")"
W=/workspace/lxx-cl/work; M=/workspace/morpheus-src
python3 -c "import sys; sys.path.insert(0,'.'); exec(open('prep_forms.py').read())"
(cd $M && MORPHLIB=stemlib src/anal/cruncher -S < $W/forms.beta > $W/morph.out 2>/dev/null)
python3 -c "import sys; sys.path.insert(0,'.'); exec(open('prep_miss.py').read())"
(cd $M && MORPHLIB=stemlib src/anal/cruncher -S -n < $W/miss.beta > $W/morph_n.out 2>/dev/null)
(cd $M && MORPHLIB=stemlib src/anal/cruncher -S < $W/caps.beta > $W/morph_caps.out 2>/dev/null)
python3 -c "import sys; sys.path.insert(0,'.'); exec(open('prep_variants.py').read())"
(cd $M && MORPHLIB=stemlib src/anal/cruncher -S -n < $W/var.beta > $W/morph_v.out 2>/dev/null)
python3 analyze.py
python3 wikt_forms.py
python3 build_clean.py
python3 enrich.py
python3 plainmeaning_clean.py
RS_RESTORE=1 python3 resegment.py
python3 brentalign.py --retrain >/dev/null   # model on the original verse pairs, used to adjust boundaries
cp $W/brentalign_model.json $W/brentalign_model_pairs_v1.json
RS_T=1.5 python3 resegment.py
python3 brentalign.py --retrain
python3 ntrefs.py
python3 lxx2012_clean.py
python3 pwa.py

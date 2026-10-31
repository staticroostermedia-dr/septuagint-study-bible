#!/usr/bin/env python3
"""LXX2012 (Michael Paul Johnson, 2012 update of Brenton; public domain, eBible.org eng-lxx2012), attached by the same Brenton reference
(it keeps Brenton's versification). Output data/en2/<Book>/<ch>.json {verse: text}."""
import json, os, re, collections, shutil
D = '/workspace/lxx-cl/site/data'
ORDER = [('GEN','Gen','Genesis'),('EXO','Exod','Exodus'),('LEV','Lev','Leviticus'),('NUM','Num','Numbers'),('DEU','Deut','Deuteronomy'),
 ('JOS','Josh','Joshua'),('JDG','Judg','Judges'),('RUT','Ruth','Ruth'),('1SA','1Sam','1 Kingdoms (1 Samuel)'),('2SA','2Sam','2 Kingdoms (2 Samuel)'),
 ('1KI','1Kgs','3 Kingdoms (1 Kings)'),('2KI','2Kgs','4 Kingdoms (2 Kings)'),('1CH','1Chr','1 Chronicles'),('2CH','2Chr','2 Chronicles'),
 ('1ES','1Esdr','1 Esdras'),('EZR','2Esdr','2 Esdras (Ezra–Nehemiah)'),('ESG','Esth','Esther'),('JDT','Jdt','Judith'),('TOB','Tob','Tobit'),
 ('1MA','1Macc','1 Maccabees'),('2MA','2Macc','2 Maccabees'),('3MA','3Macc','3 Maccabees'),('4MA','4Macc','4 Maccabees'),
 ('PSA','Ps','Psalms'),('PRM','PrMan','Prayer of Manasses'),('PRO','Prov','Proverbs'),('ECC','Eccl','Ecclesiastes'),('SOL','Song','Song of Songs'),
 ('JOB','Job','Job'),('WIS','Wis','Wisdom of Solomon'),('SIR','Sir','Sirach'),('HOS','Hos','Hosea'),('AMO','Amos','Amos'),('MIC','Mic','Micah'),
 ('JOE','Joel','Joel'),('OBA','Obad','Obadiah'),('JON','Jonah','Jonah'),('NAH','Nah','Nahum'),('HAB','Hab','Habakkuk'),('ZEP','Zeph','Zephaniah'),
 ('HAG','Hag','Haggai'),('ZEC','Zech','Zechariah'),('MAL','Mal','Malachi'),('ISA','Isa','Isaiah'),('JER','Jer','Jeremiah'),('BAR','Bar','Baruch'),
 ('LAM','Lam','Lamentations'),('EPJ','EpJer','Epistle of Jeremiah'),('EZE','Ezek','Ezekiel'),('SUS','Sus','Susanna'),('DNG','Dan','Daniel'),('BEL','Bel','Bel and the Dragon')]
CODE = {'ESG': 'EST', 'DNG': 'DAN'}
X = {}
for l in open('/workspace/lxx-audit/src/eng-lxx2012/eng-lxx2012_vpl.txt', encoding='utf-8-sig'):
    m = re.match(r'(\S+) (\d+):(\d+[a-z]*) (.*)', l.strip())
    if m: X[(m.group(1), int(m.group(2)), m.group(3))] = re.sub(r'^\(\d+(?: in KJV)?\)\s*', '', m.group(4)).replace('⌃', '').strip()
shutil.rmtree(D + '/en2', ignore_errors=True); n = tot = 0
for code, bid, name in ORDER:
    if not os.path.isdir(f'{D}/{bid}'): continue
    for f in os.listdir(f'{D}/{bid}'):
        c = int(f[:-5]); out = {}
        for v in json.load(open(f'{D}/{bid}/{f}')):
            tot += 1; t = X.get((CODE.get(code, code), c, v[0]))
            if t: out[v[0]] = t; n += 1
        if out:
            os.makedirs(f'{D}/en2/{bid}', exist_ok=True); json.dump(out, open(f'{D}/en2/{bid}/{f}', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('lxx2012: verses with LXX2012', n, 'of', tot)

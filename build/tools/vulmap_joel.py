"""Joel 3 follows the Greek numbering (Gallicantus batch): Greek (LXX) Joel 3:1-5 = Vulgate/KJV Joel 2:28-32. A data/vulmap.json entry may carry a verse
range [vb, ch, first, last]; Joel/2 shows Vulgate 2:1-27 and Joel/3 shows Vulgate 2:28-32 beside the Greek (data/vp/Joel/3.json already pairs them).
Usage: python3 build/tools/vulmap_joel.py"""
import json, os
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data')
vm = json.load(open(D + '/vulmap.json', encoding='utf-8'))
vm['Joel/2'] = [['JOL', 2, 1, 27]]; vm['Joel/3'] = [['JOL', 2, 28, 32]]
json.dump(vm, open(D + '/vulmap.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('Joel/2', vm['Joel/2'], 'Joel/3', vm['Joel/3'])

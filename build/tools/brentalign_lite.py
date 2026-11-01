"""Shared pieces of brentalign.py (stemmer, English function words, the cached IBM Model 1) without training anything."""
import json, re
ARCH = {'thee': 'you', 'thou': 'you', 'ye': 'you', 'thy': 'your', 'thine': 'your', 'hath': 'have', 'hast': 'have', 'had': 'have', 'has': 'have',
        'saith': 'say', 'said': 'say', 'doth': 'do', 'did': 'do', 'art': 'be', 'is': 'be', 'are': 'be', 'was': 'be', 'were': 'be', 'been': 'be', 'shalt': 'shall',
        'wilt': 'will', 'came': 'come', 'went': 'go', 'gave': 'give', 'given': 'give', 'took': 'take', 'taken': 'take', 'spoke': 'speak', 'spake': 'speak', 'spoken': 'speak',
        'saw': 'see', 'seen': 'see', 'made': 'make', 'brought': 'bring', 'men': 'man', 'children': 'child', 'sons': 'son', 'heard': 'hear', 'knew': 'know', 'known': 'know',
        'sat': 'sit', 'stood': 'stand', 'ate': 'eat', 'eaten': 'eat', 'begat': 'beget', 'begot': 'beget', 'smote': 'smite', 'slew': 'slay', 'slain': 'slay', 'fled': 'flee',
        'wrote': 'write', 'written': 'write', 'told': 'tell', 'sent': 'send', 'set': 'set', 'put': 'put', 'built': 'build', 'fell': 'fall', 'fallen': 'fall', 'rose': 'rise',
        'risen': 'rise', 'arose': 'arise', 'drank': 'drink', 'found': 'find', 'brethren': 'brother', 'feet': 'foot', 'women': 'woman', 'oxen': 'ox', 'kept': 'keep', 'left': 'leave', 'led': 'lead', 'dwelt': 'dwell'}
EFUNC = set('shalt wilt mayest canst wouldest couldest let ye thou thee thy thine hath hast art doth dost thereof therein whereof thereby whosoever whatsoever the a an of to and in on at by for from with into unto upon as that this these those it its he him his she her they them their we us our you your i me my mine be shall will would should may might can could do not no nor or but if then so all which who whom whose what when where there here also even yet up out over under before after against about through every any'.split())
TOK = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")
def stem(w):
    w = w.lower(); w = ARCH.get(w, w)
    for suf in ('eth', 'est', 'ing', 'edst', 'ed', 'es', 's'):
        if len(w) > len(suf) + 3 and w.endswith(suf): w = w[:-len(suf)]; break
    return w[:6]
def load_model(path='/workspace/lxx-cl/work/brentalign_model.json', both=False):
    m = json.load(open(path)); ge = {tuple(k.split('\t')): v for k, v in m['ge'].items()}
    if not both: return ge
    return ge, {tuple(k.split('\t')): v for k, v in m['eg'].items()}

#!/usr/bin/env python3
"""Build Unit 2 · Reading the Septuagint (based on Conybeare & Stock, Selections from the Septuagint, 1905, PD)
using Gallicantus's own LXX verse tokens, lexicon, and morphology."""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.join(ROOT, 'data')
W = os.path.join(ROOT, 'workbook')

lex = json.load(open(os.path.join(D, 'lexicon.json'), encoding='utf-8'))
morph = json.load(open(os.path.join(D, 'morph.json'), encoding='utf-8'))
gen37 = {str(v[0]): v for v in json.load(open(os.path.join(D, 'Gen', '37.json'), encoding='utf-8'))}

def short_parse(mi):
    m = morph[mi][1] if mi < len(morph) else ''
    return m.replace('indicative', 'ind.').replace('singular', 'sg.').replace('plural', 'pl.').replace('masculine', 'masc.').replace('feminine', 'fem.').replace('neuter', 'neut.').replace('nominative', 'nom.').replace('genitive', 'gen.').replace('dative', 'dat.').replace('accusative', 'acc.').replace('participle', 'ptcp.').replace('infinitive', 'inf.').replace('aorist', 'aor.').replace('imperfect', 'impf.').replace('present', 'pres.').replace('future', 'fut.').replace('perfect', 'perf.').replace('active', 'act.').replace('middle', 'mid.').replace('passive', 'pass.').replace('subjunctive', 'subj.').replace('imperative', 'impv.')

def build_passages_and_words(book_map, book_label, ch, vnums):
    passages, words, seen = [], [], set()
    gloss_parse = {}
    for vn in vnums:
        v = book_map[str(vn)]
        toks = []
        for t in v[1]:
            form, lid, mi = t[0], str(t[1]), t[2]
            L = lex.get(lid, [form, '', '', '', '', ''])
            lemma, gloss = L[0] or form, L[1] or form
            toks.append({'word': form, 'gloss': gloss, 'after': ' '})
            k = form.rstrip(',.;·')
            if k not in gloss_parse:
                gloss_parse[k] = {'lemma': lemma, 'parse': short_parse(mi)}
            if form not in gloss_parse:
                gloss_parse[form] = {'lemma': lemma, 'parse': short_parse(mi)}
            if lemma not in seen and gloss:
                seen.add(lemma)
                words.append([lemma, gloss])
        passages.append({'ref': f'{book_label} {ch}:{vn}', 'tokens': toks})
    return passages, words[:18], gloss_parse

# Part I: Story of Joseph (Genesis 37:1-36) — 8 lessons + 1 Review lesson
LESSONS_SPEC = [
  {
    'id': '1', 'roman': 'I', 'verses': 'Gen 37:1–3', 'vnums': [1, 2, 3],
    'title': 'Jacob in Canaan; Joseph’s tunic',
    'about': 'κατοικέω vs. παροικέω; analytic imperfect ἦν ποιμαίνων; παρά for comparison',
    'patternHeading': 'Notes on Genesis 37:1–3',
    'patternText': 'Jacob dwells in Canaan where his father sojourned; Joseph, seventeen years old, shepherds the flock and receives a variegated tunic from his father.',
    'patternRows': [
      ['Κατῴκει δὲ Ἰακὼβ ἐν τῇ γῇ', 'And Jacob dwelt in the land.'],
      ['ἦν ποιμαίνων τὰ πρόβατα', 'he was shepherding the sheep.'],
      ['ἠγάπα τὸν Ἰωσὴφ παρὰ πάντας', 'he loved Joseph more than all.'],
    ],
    'rules': [
      {'title': 'κατοικεῖν vs. παροικεῖν', 'rule': 'κατοικεῖν here signifies a more permanent residence than παροικεῖν. Jacob dwelt where Abraham only sojourned. From meaning a settlement of Jews in a foreign country, παροικία came to mean an ecclesiastical district or diocese — the origin of our word parish.'},
      {'title': 'Analytic Imperfect (ἦν ποιμαίνων)', 'rule': 'ἦν ποιμαίνων is the analytic (periphrastic) form of the imperfect = ἐποίμαινε. Such forms occur in all stages of the language and are especially common in the LXX and N.T.'},
      {'title': 'Comparison with παρά (παρὰ πάντας)', 'rule': 'παρὰ πάντας means more than all. The Hebrew language has no comparative degree of adjectives, and the LXX frequently expresses comparison by παρά or ἐκ with the positive.'},
    ],
    'choices': [
      {'key': 'c1', 'prompt': 'Choose the English.', 'greek': 'Κατῴκει δὲ Ἰακὼβ ἐν τῇ γῇ Χαναάν', 'options': ['And Jacob dwelt in the land of Canaan.', 'And Jacob fled from the land of Canaan.', 'And Jacob bought the land of Canaan.', 'And Jacob sent Joseph to Canaan.'], 'answer': 'And Jacob dwelt in the land of Canaan.', 'yes': 'Yes. κατῴκει is imperfect of κατοικέω (dwelt).', 'no': 'Check κατῴκει (dwelt) and ἐν τῇ γῇ (in the land).'},
      {'key': 'c2', 'prompt': 'Choose the English.', 'greek': 'ἦν ποιμαίνων τὰ πρόβατα τοῦ πατρὸς αὐτοῦ', 'options': ['He was feeding his father’s sheep.', 'He sold his father’s sheep.', 'He counted his father’s sheep.', 'His father fed the sheep.'], 'answer': 'He was feeding his father’s sheep.', 'yes': 'Yes. ἦν ποιμαίνων is the periphrastic imperfect: was feeding / shepherding.', 'no': 'ἦν + present participle ποιμαίνων = was feeding/shepherding.'},
    ],
    'writes': [
      {'key': 'w1', 'english': 'Jacob dwelt in the land.', 'tiles': ['Ἰακὼβ', 'κατῴκει', 'ἐν', 'τῇ', 'γῇ'], 'target': ['Ἰακὼβ', 'κατῴκει', 'ἐν', 'τῇ', 'γῇ'], 'yes': 'Yes. Ἰακὼβ κατῴκει ἐν τῇ γῇ.', 'no': 'Order: Ἰακὼβ κατῴκει ἐν τῇ γῇ.'},
      {'key': 'w2', 'english': 'He loved Joseph more than all his sons.', 'tiles': ['ἠγάπα', 'τὸν', 'Ἰωσὴφ', 'παρὰ', 'πάντας', 'τοὺς', 'υἱοὺς', 'αὐτοῦ'], 'target': ['ἠγάπα', 'τὸν', 'Ἰωσὴφ', 'παρὰ', 'πάντας', 'τοὺς', 'υἱοὺς', 'αὐτοῦ'], 'yes': 'Yes. παρὰ πάντας = more than all.', 'no': 'Order: ἠγάπα τὸν Ἰωσὴφ παρὰ πάντας τοὺς υἱοὺς αὐτοῦ.'},
    ],
    'practice': [
      {'id': 'p1', 'kind': 'choose', 'ref': 'Gen 37:1', 'greek': 'οὗ παρῴκησεν ὁ πατὴρ αὐτοῦ', 'prompt': 'Choose the English.', 'options': ['where his father sojourned', 'where his father died', 'from which his father came', 'where his brothers dwelt'], 'answer': 'where his father sojourned', 'yes': 'Yes. παροικέω = dwell as a stranger / sojourn.', 'no': 'παρῴκησεν is aorist of παροικέω (sojourned).'},
      {'id': 'p2', 'kind': 'choose', 'ref': 'Gen 37:3', 'greek': 'ἐποίησε δὲ αὐτῷ χιτῶνα ποικίλον', 'prompt': 'Choose the English.', 'options': ['and he made for him a coat of many colors', 'and he gave him a flock of sheep', 'and he sent him to his brothers', 'and he made a covenant with him'], 'answer': 'and he made for him a coat of many colors', 'yes': 'Yes. χιτῶνα ποικίλον = a variegated tunic / coat of many colors.', 'no': 'χιτών = tunic/coat; ποικίλος = variegated / of many colors.'},
      {'id': 'p3', 'kind': 'match', 'ref': 'Gen 37:1–3', 'prompt': 'Match each Greek phrase to its English.', 'pairs': [
        {'id': 'a', 'greek': 'ἐν τῇ γῇ', 'english': 'in the land'},
        {'id': 'b', 'greek': 'τὰ πρόβατα', 'english': 'the sheep'},
        {'id': 'c', 'greek': 'παρὰ πάντας', 'english': 'more than all'},
        {'id': 'd', 'greek': 'χιτῶνα ποικίλον', 'english': 'a coat of many colors'},
      ], 'yes': 'Yes. All four phrases match.', 'no': 'Check παρὰ πάντας (more than all) and τὰ πρόβατα (the sheep).'},
      {'id': 'p4', 'kind': 'tiles', 'ref': 'Gen 37:3', 'english': '“He made for him a coat of many colors.”', 'prompt': 'Build this Greek clause:', 'tiles': ['ἐποίησε', 'δὲ', 'αὐτῷ', 'χιτῶνα', 'ποικίλον'], 'target': ['ἐποίησε', 'δὲ', 'αὐτῷ', 'χιτῶνα', 'ποικίλον'], 'yes': 'Yes. ἐποίησε δὲ αὐτῷ χιτῶνα ποικίλον.', 'no': 'Order: ἐποίησε δὲ αὐτῷ χιτῶνα ποικίλον.'},
    ],
  },
  {
    'id': '2', 'roman': 'II', 'verses': 'Gen 37:4–7', 'vnums': [4, 5, 6, 7],
    'title': 'The brothers’ envy; the dream of the sheaves',
    'about': 'ἐκ πάντων for comparison; cognate accusative ἐνυπνιασθεὶς ἐνύπνιον; genitive after ἀκούω',
    'patternHeading': 'Notes on Genesis 37:4–7',
    'patternText': 'Joseph’s brothers see their father’s favor and hate him; Joseph dreams of binding sheaves in the field.',
    'patternRows': [
      ['αὐτὸν ὁ πατὴρ φιλεῖ ἐκ πάντων', 'his father loves him more than all.'],
      ['Ἐνυπνιασθεὶς δὲ Ἰωσὴφ ἐνύπνιον', 'And Joseph having dreamed a dream.'],
      ['ἀκούσατε τοῦ ἐνυπνίου τούτου', 'Hear this dream.'],
    ],
    'rules': [
      {'title': 'ἐκ πάντων = παρὰ πάντας', 'rule': 'ἐκ πάντων in v. 4 is a different rendering of the same Hebrew original as παρὰ πάντας in v. 3, both expressing the comparative: more than all.'},
      {'title': 'Cognate Accusative (ἐνυπνιασθεὶς ἐνύπνιον)', 'rule': 'A verb may take an accusative noun of kindred meaning (cognate accusative): ἐνυπνιασθεὶς ἐνύπνιον, having dreamed a dream. This Greek idiom closely matches the Hebrew.'},
      {'title': 'Genitive After ἀκούω', 'rule': 'ἀκούω (I hear) regularly takes the genitive of the sound or speech heard: ἀκούσατε τοῦ ἐνυπνίου τούτου (hear this dream).'},
    ],
    'choices': [
      {'key': 'c1', 'prompt': 'Choose the English.', 'greek': 'ἐμίσησαν αὐτὸν καὶ οὐκ ἐδύναντο λαλεῖν αὐτῷ οὐδὲν εἰρηνικόν', 'options': ['They hated him and could not speak anything peaceable to him.', 'They loved him and spoke peaceably to him.', 'They feared him and hid from him.', 'They sent him away in peace.'], 'answer': 'They hated him and could not speak anything peaceable to him.', 'yes': 'Yes. ἐμίσησαν (hated) + οὐκ ἐδύναντο λαλεῖν (could not speak).', 'no': 'Check ἐμίσησαν (hated) and εἰρηνικόν (peaceable).'},
      {'key': 'c2', 'prompt': 'Choose the English.', 'greek': 'ἀνέστη τὸ ἐμὸν δράγμα καὶ ὠρθώθη', 'options': ['My sheaf arose and stood upright.', 'My sheaf fell down to the ground.', 'Your sheaves gathered around the field.', 'We were binding sheaves in the field.'], 'answer': 'My sheaf arose and stood upright.', 'yes': 'Yes. ἀνέστη (arose) and ὠρθώθη (stood upright).', 'no': 'δράγμα = sheaf; ἀνέστη = stood up / arose.'},
    ],
    'writes': [
      {'key': 'w1', 'english': 'Hear this dream.', 'tiles': ['ἀκούσατε', 'τοῦ', 'ἐνυπνίου', 'τούτου'], 'target': ['ἀκούσατε', 'τοῦ', 'ἐνυπνίου', 'τούτου'], 'yes': 'Yes. ἀκούσατε τοῦ ἐνυπνίου τούτου.', 'no': 'Order: ἀκούσατε τοῦ ἐνυπνίου τούτου.'},
      {'key': 'w2', 'english': 'My sheaf arose.', 'tiles': ['ἀνέστη', 'τὸ', 'ἐμὸν', 'δράγμα'], 'target': ['ἀνέστη', 'τὸ', 'ἐμὸν', 'δράγμα'], 'yes': 'Yes. ἀνέστη τὸ ἐμὸν δράγμα.', 'no': 'Order: ἀνέστη τὸ ἐμὸν δράγμα.'},
    ],
    'practice': [
      {'id': 'p1', 'kind': 'choose', 'ref': 'Gen 37:5', 'greek': 'ἀπήγγειλεν αὐτὸ τοῖς ἀδελφοῖς αὐτοῦ', 'prompt': 'Choose the English.', 'options': ['he reported it to his brothers', 'he hid it from his brothers', 'he asked his brothers about it', 'his brothers reported it to him'], 'answer': 'he reported it to his brothers', 'yes': 'Yes. ἀπήγγειλεν = reported / told.', 'no': 'ἀπαγγέλλω = report, declare; τοῖς ἀδελφοῖς = dat. pl.'},
      {'id': 'p2', 'kind': 'match', 'ref': 'Gen 37:4–7', 'prompt': 'Match each Greek word to its meaning.', 'pairs': [
        {'id': 'a', 'greek': 'ἐνύπνιον', 'english': 'dream'},
        {'id': 'b', 'greek': 'δράγμα', 'english': 'sheaf'},
        {'id': 'c', 'greek': 'πεδίον', 'english': 'field / plain'},
        {'id': 'd', 'greek': 'ἐμίσησαν', 'english': 'they hated'},
      ], 'yes': 'Yes. All four match.', 'no': 'Check δράγμα (sheaf) and πεδίον (field).'},
      {'id': 'p3', 'kind': 'tiles', 'ref': 'Gen 37:6', 'english': '“Hear this dream which I have dreamed.”', 'prompt': 'Build this Greek clause:', 'tiles': ['ἀκούσατε', 'τοῦ', 'ἐνυπνίου', 'τούτου', 'οὗ', 'ἐνυπνιάσθην'], 'target': ['ἀκούσατε', 'τοῦ', 'ἐνυπνίου', 'τούτου', 'οὗ', 'ἐνυπνιάσθην'], 'yes': 'Yes. Notice relative attraction: οὗ (gen.) attracted to τοῦ ἐνυπνίου.', 'no': 'Order: ἀκούσατε τοῦ ἐνυπνίου τούτου οὗ ἐνυπνιάσθην.'},
    ],
  },
  {
    'id': '3', 'roman': 'III', 'verses': 'Gen 37:8–11', 'vnums': [8, 9, 10, 11],
    'title': 'The sun, moon, and eleven stars',
    'about': 'Participle + finite verb (βασιλεύων βασιλεύσεις); Hebraism προσέθεντο ἔτι μισεῖν; Luke 2:19 parallel',
    'patternHeading': 'Notes on Genesis 37:8–11',
    'patternText': 'Joseph tells a second dream of sun, moon, and eleven stars bowing down; his brothers hate him still more, while his father keeps the saying.',
    'patternRows': [
      ['μὴ βασιλεύων βασιλεύσεις ἐφʼ ἡμᾶς;', 'Shalt thou indeed reign over us?'],
      ['προσέθεντο ἔτι μισεῖν αὐτόν', 'they hated him yet the more.'],
      ['ὁ δὲ πατὴρ αὐτοῦ διετήρησε τὸ ῥῆμα', 'but his father kept the saying.'],
    ],
    'rules': [
      {'title': 'Participle + Finite Verb (βασιλεύων βασιλεύσεις)', 'rule': 'The LXX renders the Hebrew infinitive absolute by a participle of the same verb: βασιλεύων βασιλεύσεις (shalt thou indeed reign), ἐλθόντες ἐλευσόμεθα (shall we indeed come).'},
      {'title': 'Hebraism: προσέθεντο ἔτι μισεῖν', 'rule': 'προσέθεντο ἔτι μισεῖν literally means they added yet to hate = they hated him still more — a Hebraism very common throughout the LXX.'},
      {'title': 'Echo in the New Testament (v. 11)', 'rule': 'ὁ δὲ πατὴρ αὐτοῦ διετήρησε τὸ ῥῆμα (his father kept the saying): Luke 2:19 and 2:51 (Mary kept all these sayings in her heart) are modelled directly on this Septuagint verse.'},
    ],
    'choices': [
      {'key': 'c1', 'prompt': 'Choose the English.', 'greek': 'προσέθεντο ἔτι μισεῖν αὐτόν', 'options': ['They hated him yet the more.', 'They ceased to hate him.', 'They spoke kindly to him.', 'They bowed down to him.'], 'answer': 'They hated him yet the more.', 'yes': 'Yes. προστίθημι + infinitive = do again / do still more.', 'no': 'προσέθεντο ἔτι μισεῖν = literally “added yet to hate” = hated still more.'},
      {'key': 'c2', 'prompt': 'Choose the English.', 'greek': 'ὁ δὲ πατὴρ αὐτοῦ διετήρησε τὸ ῥῆμα', 'options': ['But his father kept the saying.', 'But his father forgot the dream.', 'But his father rebuked the brothers.', 'And his father wept for him.'], 'answer': 'But his father kept the saying.', 'yes': 'Yes. διατηρέω = keep carefully, observe.', 'no': 'διετήρησε = kept; τὸ ῥῆμα = the word/saying.'},
    ],
    'writes': [
      {'key': 'w1', 'english': 'They hated him yet the more.', 'tiles': ['προσέθεντο', 'ἔτι', 'μισεῖν', 'αὐτόν'], 'target': ['προσέθεντο', 'ἔτι', 'μισεῖν', 'αὐτόν'], 'yes': 'Yes. προσέθεντο ἔτι μισεῖν αὐτόν.', 'no': 'Order: προσέθεντο ἔτι μισεῖν αὐτόν.'},
      {'key': 'w2', 'english': 'His father kept the saying.', 'tiles': ['ὁ', 'πατὴρ', 'αὐτοῦ', 'διετήρησε', 'τὸ', 'ῥῆμα'], 'target': ['ὁ', 'πατὴρ', 'αὐτοῦ', 'διετήρησε', 'τὸ', 'ῥῆμα'], 'yes': 'Yes. ὁ πατὴρ αὐτοῦ διετήρησε τὸ ῥῆμα.', 'no': 'Order: ὁ πατὴρ αὐτοῦ διετήρησε τὸ ῥῆμα.'},
    ],
    'practice': [
      {'id': 'p1', 'kind': 'choose', 'ref': 'Gen 37:9', 'greek': 'ὁ ἥλιος καὶ ἡ σελήνη καὶ ἕνδεκα ἀστέρες προσεκύνουν με', 'prompt': 'Choose the English.', 'options': ['the sun and the moon and eleven stars were bowing down to me', 'the sun and the moon shone upon me', 'eleven stars fell from heaven', 'the sun and moon fled before me'], 'answer': 'the sun and the moon and eleven stars were bowing down to me', 'yes': 'Yes. προσκυνέω = bow down / do obeisance.', 'no': 'ἥλιος = sun, σελήνη = moon, ἀστέρες = stars, προσεκύνουν = bowed down.'},
      {'id': 'p2', 'kind': 'match', 'ref': 'Gen 37:8–11', 'prompt': 'Match each Greek word to its meaning.', 'pairs': [
        {'id': 'a', 'greek': 'ὁ ἥλιος', 'english': 'the sun'},
        {'id': 'b', 'greek': 'ἡ σελήνη', 'english': 'the moon'},
        {'id': 'c', 'greek': 'ἀστέρες', 'english': 'stars'},
        {'id': 'd', 'greek': 'τὸ ῥῆμα', 'english': 'the saying / word'},
      ], 'yes': 'Yes. All four match.', 'no': 'Check σελήνη (moon) and ἀστέρες (stars).'},
      {'id': 'p3', 'kind': 'tiles', 'ref': 'Gen 37:11', 'english': '“But his father kept the saying.”', 'prompt': 'Build this Greek clause:', 'tiles': ['ὁ', 'δὲ', 'πατὴρ', 'αὐτοῦ', 'διετήρησε', 'τὸ', 'ῥῆμα'], 'target': ['ὁ', 'δὲ', 'πατὴρ', 'αὐτοῦ', 'διετήρησε', 'τὸ', 'ῥῆμα'], 'yes': 'Yes. ὁ δὲ πατὴρ αὐτοῦ διετήρησε τὸ ῥῆμα.', 'no': 'Order: ὁ δὲ πατὴρ αὐτοῦ διετήρησε τὸ ῥῆμα.'},
    ],
  },
  {
    'id': '4', 'roman': 'IV', 'verses': 'Gen 37:12–17', 'vnums': [12, 13, 14, 15, 16, 17],
    'title': 'Sent to Shechem and Dothan',
    'about': 'εἰς for rest in a place (εἰς Συχέμ); κοιλάς (vale); intransitive ἀπαίρω (depart)',
    'patternHeading': 'Notes on Genesis 37:12–17',
    'patternText': 'Israel sends Joseph from the valley of Hebron to check on his brothers; a stranger in the field directs him to Dothan.',
    'patternRows': [
      ['Τούς ἀδελφούς μου ζητῶ', 'I am seeking my brothers.'],
      ['Ἀπήρκασιν ἐντεῦθεν', 'They have departed from here.'],
      ['Πορευθῶμεν εἰς Δωθαΐμ', 'Let us go to Dothan.'],
    ],
    'rules': [
      {'title': 'εἰς for Location (εἰς Συχέμ)', 'rule': 'In the LXX and N.T., εἰς frequently encroaches on ἐν to denote rest in a place: βόσκειν εἰς Συχέμ (to feed the sheep at Shechem).'},
      {'title': 'Intransitive ἀπήρκασιν (they have departed)', 'rule': 'ἀπήρκασιν (perf. act. of ἀπαίρω) means they have departed. This intransitive use originated from an ellipse of ναῦς (ships) or στρατόν (camp) — to strike camp and move on.'},
      {'title': 'Hortatory Subjunctive (Πορευθῶμεν)', 'rule': 'The 1st person plural subjunctive expresses an exhortation (let us ...): πορευθῶμεν εἰς Δωθαΐμ (let us go to Dothan).'},
    ],
    'choices': [
      {'key': 'c1', 'prompt': 'Choose the English.', 'greek': 'Τοὺς ἀδελφούς μου ζητῶ', 'options': ['I am seeking my brothers.', 'My brothers are seeking me.', 'I have found my brothers.', 'Tell my brothers I am here.'], 'answer': 'I am seeking my brothers.', 'yes': 'Yes. ζητῶ = I seek; τοὺς ἀδελφούς μου = acc. pl. direct object.', 'no': 'ζητῶ is 1st sing. present (I seek).'},
      {'key': 'c2', 'prompt': 'Choose the English.', 'greek': 'Ἀπήρκασιν ἐντεῦθεν', 'options': ['They have departed from here.', 'They are dwelling here.', 'They have returned here.', 'They are feeding the flock here.'], 'answer': 'They have departed from here.', 'yes': 'Yes. ἀπήρκασιν = they have departed; ἐντεῦθεν = from here.', 'no': 'ἀπαίρω (intrans.) = depart; ἐντεῦθεν = hence / from here.'},
    ],
    'writes': [
      {'key': 'w1', 'english': 'I am seeking my brothers.', 'tiles': ['τοὺς', 'ἀδελφούς', 'μου', 'ζητῶ'], 'target': ['τοὺς', 'ἀδελφούς', 'μου', 'ζητῶ'], 'yes': 'Yes. τοὺς ἀδελφούς μου ζητῶ.', 'no': 'Order: τοὺς ἀδελφούς μου ζητῶ.'},
      {'key': 'w2', 'english': 'Let us go to Dothan.', 'tiles': ['πορευθῶμεν', 'εἰς', 'Δωθαΐμ'], 'target': ['πορευθῶμεν', 'εἰς', 'Δωθαΐμ'], 'yes': 'Yes. πορευθῶμεν εἰς Δωθαΐμ.', 'no': 'Order: πορευθῶμεν εἰς Δωθαΐμ.'},
    ],
    'practice': [
      {'id': 'p1', 'kind': 'choose', 'ref': 'Gen 37:15', 'greek': 'Εὗρεν δὲ αὐτὸν ἄνθρωπος πλανώμενον ἐν τῷ πεδίῳ', 'prompt': 'Choose the English.', 'options': ['And a man found him wandering in the field.', 'And he found a man working in the field.', 'And his brothers found him in the valley.', 'And a man sent him out of the field.'], 'answer': 'And a man found him wandering in the field.', 'yes': 'Yes. πλανώμενον = wandering (pres. mid./pass. ptcp. of πλανάω).', 'no': 'εὗρεν = found; πλανώμενον = wandering.'},
      {'id': 'p2', 'kind': 'match', 'ref': 'Gen 37:12–17', 'prompt': 'Match each Greek word to its meaning.', 'pairs': [
        {'id': 'a', 'greek': 'ζητῶ', 'english': 'I seek'},
        {'id': 'b', 'greek': 'ἐντεῦθεν', 'english': 'from here'},
        {'id': 'c', 'greek': 'κοιλάς', 'english': 'valley / vale'},
        {'id': 'd', 'greek': 'πλανώμενον', 'english': 'wandering'},
      ], 'yes': 'Yes. All four match.', 'no': 'Check κοιλάς (valley) and ἐντεῦθεν (from here).'},
      {'id': 'p3', 'kind': 'tiles', 'ref': 'Gen 37:16', 'english': '“I am seeking my brothers.”', 'prompt': 'Build this Greek clause:', 'tiles': ['τοὺς', 'ἀδελφούς', 'μου', 'ζητῶ'], 'target': ['τοὺς', 'ἀδελφούς', 'μου', 'ζητῶ'], 'yes': 'Yes. τοὺς ἀδελφούς μου ζητῶ.', 'no': 'Order: τοὺς ἀδελφούς μου ζητῶ.'},
    ],
  },
  {
    'id': '5', 'roman': 'V', 'verses': 'Gen 37:18–22', 'vnums': [18, 19, 20, 21, 22],
    'title': 'The plot and Reuben’s intervention',
    'about': 'λάκκος (pit / cistern); Hebraism εἰς ψυχήν; vivid subjunctive ὅπως ἐξέληται',
    'patternHeading': 'Notes on Genesis 37:18–22',
    'patternText': 'Seeing Joseph from afar, the brothers conspire to kill him, but Reuben persuades them to cast him into a pit so he may rescue him.',
    'patternRows': [
      ['Ἰδοὺ ὁ ἐνυπνιαστὴς ἐκεῖνος ἔρχεται', 'Behold, that dreamer comes.'],
      ['μὴ πατάξωμεν αὐτὸν εἰς ψυχήν', 'let us not kill him (lit. strike him unto life).'],
      ['ὅπως ἐξέληται αὐτὸν ἐκ τῶν χειρῶν αὐτῶν', 'so that he may deliver him out of their hands.'],
    ],
    'rules': [
      {'title': 'λάκκος (pit / cistern)', 'rule': 'λάκκος (pit) is connected with Latin lacus and lacuna, and is used in Greek authors for large underground cisterns or tanks.'},
      {'title': 'Hebraism: πατάξωμεν αὐτὸν εἰς ψυχήν', 'rule': 'εἰς ψυχήν (literally unto life) means so as to slay him — a direct rendering of the Hebrew idiom for taking a person’s life.'},
      {'title': 'Vivid Subjunctive (ὅπως ἐξέληται)', 'rule': 'ὅπως ἐξέληται αὐτόν (so that he may deliver him): primary sequence (subjunctive) after a historic tense vividly presents the intention in the mind of the speaker.'},
    ],
    'choices': [
      {'key': 'c1', 'prompt': 'Choose the English.', 'greek': 'Ἰδοὺ ὁ ἐνυπνιαστὴς ἐκεῖνος ἔρχεται', 'options': ['Behold, that dreamer comes.', 'Behold, our brother is departing.', 'Behold, the father is calling us.', 'Behold, a wild beast is coming.'], 'answer': 'Behold, that dreamer comes.', 'yes': 'Yes. ἐνυπνιαστής = dreamer; ἐκεῖνος = that (contemptuous).', 'no': 'ἰδού = behold; ἐνυπνιαστής = dreamer.'},
      {'key': 'c2', 'prompt': 'Choose the English.', 'greek': 'μὴ ἐκχέητε αἷμα', 'options': ['Do not shed blood.', 'Do not fear him.', 'Do not sell him.', 'Do not tell our father.'], 'answer': 'Do not shed blood.', 'yes': 'Yes. μή + aorist subjunctive ἐκχέητε = prohibition (do not shed).', 'no': 'ἐκχέω = pour out / shed; αἷμα = blood.'},
    ],
    'writes': [
      {'key': 'w1', 'english': 'Do not shed blood.', 'tiles': ['μὴ', 'ἐκχέητε', 'αἷμα'], 'target': ['μὴ', 'ἐκχέητε', 'αἷμα'], 'yes': 'Yes. μὴ ἐκχέητε αἷμα.', 'no': 'Order: μὴ ἐκχέητε αἷμα.'},
      {'key': 'w2', 'english': 'Behold, that dreamer comes.', 'tiles': ['ἰδοὺ', 'ὁ', 'ἐνυπνιαστὴς', 'ἐκεῖνος', 'ἔρχεται'], 'target': ['ἰδοὺ', 'ὁ', 'ἐνυπνιαστὴς', 'ἐκεῖνος', 'ἔρχεται'], 'yes': 'Yes. ἰδοὺ ὁ ἐνυπνιαστὴς ἐκεῖνος ἔρχεται.', 'no': 'Order: ἰδοὺ ὁ ἐνυπνιαστὴς ἐκεῖνος ἔρχεται.'},
    ],
    'practice': [
      {'id': 'p1', 'kind': 'choose', 'ref': 'Gen 37:22', 'greek': 'ἐμβάλετε αὐτὸν εἰς τὸν λάκκον τοῦτον', 'prompt': 'Choose the English.', 'options': ['cast him into this pit', 'draw him out of this pit', 'lead him into this valley', 'bind him in this field'], 'answer': 'cast him into this pit', 'yes': 'Yes. ἐμβάλετε = cast in (2nd aor. impv.); λάκκος = pit.', 'no': 'ἐμβάλλω = throw/cast into; λάκκος = pit.'},
      {'id': 'p2', 'kind': 'match', 'ref': 'Gen 37:18–22', 'prompt': 'Match each Greek word to its meaning.', 'pairs': [
        {'id': 'a', 'greek': 'λάκκος', 'english': 'pit / cistern'},
        {'id': 'b', 'greek': 'αἷμα', 'english': 'blood'},
        {'id': 'c', 'greek': 'ἐνυπνιαστής', 'english': 'dreamer'},
        {'id': 'd', 'greek': 'χείρ', 'english': 'hand'},
      ], 'yes': 'Yes. All four match.', 'no': 'Check λάκκος (pit) and αἷμα (blood).'},
      {'id': 'p3', 'kind': 'tiles', 'ref': 'Gen 37:22', 'english': '“Do not shed blood.”', 'prompt': 'Build this Greek clause:', 'tiles': ['μὴ', 'ἐκχέητε', 'αἷμα'], 'target': ['μὴ', 'ἐκχέητε', 'αἷμα'], 'yes': 'Yes. μὴ ἐκχέητε αἷμα.', 'no': 'Order: μὴ ἐκχέητε αἷμα.'},
    ],
  },
  {
    'id': '6', 'roman': 'VI', 'verses': 'Gen 37:23–28', 'vnums': [23, 24, 25, 26, 27, 28],
    'title': 'Thrown into the pit; sold to the Ishmaelites',
    'about': '3rd plur. imperative in -ωσαν (ἔστωσαν); ἤκουσαν meaning obeyed; imperfect παρεπορεύοντο',
    'patternHeading': 'Notes on Genesis 37:23–28',
    'patternText': 'The brothers strip Joseph of his tunic, throw him into an empty pit, and at Judah’s urging sell him to Midianite/Ishmaelite merchants for twenty pieces of gold.',
    'patternRows': [
      ['ὁ δὲ λάκκος κενός ὕδωρ οὐκ εἶχεν', 'and the pit was empty, it had no water.'],
      ['ἀδελφὸς γὰρ ἡμῶν καὶ σὰρξ ἡμῶν ἐστιν', 'for he is our brother and our flesh.'],
      ['ἤκουσαν δὲ οἱ ἀδελφοὶ αὐτοῦ', 'and his brothers hearkened / obeyed.'],
    ],
    'rules': [
      {'title': 'Imperative in -ωσαν (ἔστωσαν)', 'rule': 'In the LXX, the 3rd person plural imperative regularly ends in -τωσαν / -ωσαν rather than classical -ντων: αἱ χεῖρες ἡμῶν μὴ ἔστωσαν ἐπʼ αὐτόν (let not our hands be upon him).'},
      {'title': 'ἤκουσαν = Obeyed', 'rule': 'ἤκουσαν in v. 27 means not only heard, but obeyed — like English hearken (compare classical ὑπακούω).'},
      {'title': 'Descriptive Imperfect (παρεπορεύοντο)', 'rule': 'παρεπορεύοντο (were passing by) paints the action in progress: the Midianite merchants had been seen in the distance and were now passing by.'},
    ],
    'choices': [
      {'key': 'c1', 'prompt': 'Choose the English.', 'greek': 'ὁ δὲ λάκκος κενός ὕδωρ οὐκ εἶχεν', 'options': ['And the pit was empty; it had no water.', 'And the pit was deep and full of water.', 'And the cistern was broken.', 'And they drew water from the pit.'], 'answer': 'And the pit was empty; it had no water.', 'yes': 'Yes. κενός = empty; ὕδωρ = water.', 'no': 'κενός = empty; ὕδωρ οὐκ εἶχεν = had no water.'},
      {'key': 'c2', 'prompt': 'Choose the English.', 'greek': 'ἀδελφὸς γὰρ ἡμῶν καὶ σὰρξ ἡμῶν ἐστιν', 'options': ['For he is our brother and our flesh.', 'For he is our father’s favorite son.', 'For our brothers have departed.', 'For his flesh is weak.'], 'answer': 'For he is our brother and our flesh.', 'yes': 'Yes. σάρξ = flesh; ἡμῶν = of us / our.', 'no': 'ἀδελφός = brother; σάρξ = flesh.'},
    ],
    'writes': [
      {'key': 'w1', 'english': 'He is our brother and our flesh.', 'tiles': ['ἀδελφὸς', 'ἡμῶν', 'καὶ', 'σὰρξ', 'ἡμῶν', 'ἐστιν'], 'target': ['ἀδελφὸς', 'ἡμῶν', 'καὶ', 'σὰρξ', 'ἡμῶν', 'ἐστιν'], 'yes': 'Yes. ἀδελφὸς ἡμῶν καὶ σὰρξ ἡμῶν ἐστιν.', 'no': 'Order: ἀδελφὸς ἡμῶν καὶ σὰρξ ἡμῶν ἐστιν.'},
      {'key': 'w2', 'english': 'And his brothers obeyed.', 'tiles': ['ἤκουσαν', 'δὲ', 'οἱ', 'ἀδελφοὶ', 'αὐτοῦ'], 'target': ['ἤκουσαν', 'δὲ', 'οἱ', 'ἀδελφοὶ', 'αὐτοῦ'], 'yes': 'Yes. ἤκουσαν δὲ οἱ ἀδελφοὶ αὐτοῦ.', 'no': 'Order: ἤκουσαν δὲ οἱ ἀδελφοὶ αὐτοῦ.'},
    ],
    'practice': [
      {'id': 'p1', 'kind': 'choose', 'ref': 'Gen 37:28', 'greek': 'ἀπέδοντο τὸν Ἰωσὴφ τοῖς Ἰσμαηλίταις', 'prompt': 'Choose the English.', 'options': ['they sold Joseph to the Ishmaelites', 'they gave Joseph to his father', 'they brought Joseph out of Egypt', 'the Ishmaelites rescued Joseph'], 'answer': 'they sold Joseph to the Ishmaelites', 'yes': 'Yes. ἀποδίδομαι (middle) = sell.', 'no': 'ἀπέδοντο (2nd aor. mid. of ἀποδίδωμι) = they sold.'},
      {'id': 'p2', 'kind': 'match', 'ref': 'Gen 37:23–28', 'prompt': 'Match each Greek word to its meaning.', 'pairs': [
        {'id': 'a', 'greek': 'κενός', 'english': 'empty'},
        {'id': 'b', 'greek': 'ὕδωρ', 'english': 'water'},
        {'id': 'c', 'greek': 'ἔμποροι', 'english': 'merchants'},
        {'id': 'd', 'greek': 'ἀπέδοντο', 'english': 'they sold'},
      ], 'yes': 'Yes. All four match.', 'no': 'Check κενός (empty) and ἔμποροι (merchants).'},
      {'id': 'p3', 'kind': 'tiles', 'ref': 'Gen 37:24', 'english': '“It had no water.”', 'prompt': 'Build this Greek clause:', 'tiles': ['ὕδωρ', 'οὐκ', 'εἶχεν'], 'target': ['ὕδωρ', 'οὐκ', 'εἶχεν'], 'yes': 'Yes. ὕδωρ οὐκ εἶχεν.', 'no': 'Order: ὕδωρ οὐκ εἶχεν.'},
    ],
  },
  {
    'id': '7', 'roman': 'VII', 'verses': 'Gen 37:29–32', 'vnums': [29, 30, 31, 32],
    'title': 'Reuben’s grief; the blood-stained tunic',
    'about': 'Deliberative present ποῦ πορεύομαι; partitive genitive ἔριφον αἰγῶν; imperative ἐπίγνωθι',
    'patternHeading': 'Notes on Genesis 37:29–32',
    'patternText': 'Reuben returns to find the pit empty and tears his garments; the brothers dip Joseph’s tunic in goat’s blood and send it to Jacob.',
    'patternRows': [
      ['Τὸ παιδάριον οὐκ ἔστιν', 'The boy is not (there).'],
      ['ἐγὼ δὲ ποῦ πορεύομαι ἔτι;', 'and I, whither am I yet to go?'],
      ['Τοῦτον εὕρομεν ἐπίγνωθι εἰ χιτὼν τοῦ υἱοῦ σού ἐστιν', 'This we have found: recognize whether it is your son’s coat.'],
    ],
    'rules': [
      {'title': 'Deliberative Present (ποῦ πορεύομαι;)', 'rule': 'In vivid questions of perplexity, the present indicative can be used like a deliberative subjunctive: ἐγὼ δὲ ποῦ πορεύομαι ἔτι; (whither am I to go?).'},
      {'title': 'Genitive of Material / Species (ἔριφον αἰγῶν)', 'rule': 'ἔριφον αἰγῶν (a kid of the goats) is a frequent LXX idiom for specifying the kind of animal (compare Judg. 6:19; 1 Sam. 16:20).'},
      {'title': 'Root Aorist Imperative (ἐπίγνωθι)', 'rule': 'γινώσκω (and its compound ἐπιγινώσκω, recognize) forms a root 2nd aorist imperative in -θι: ἐπίγνωθι (recognize / know for certain!).'},
    ],
    'choices': [
      {'key': 'c1', 'prompt': 'Choose the English.', 'greek': 'Τὸ παιδάριον οὐκ ἔστιν', 'options': ['The boy is not there.', 'The boy is sleeping.', 'The boy has returned.', 'The boy is weeping.'], 'answer': 'The boy is not there.', 'yes': 'Yes. παιδάριον = lad/boy; οὐκ ἔστιν = is not.', 'no': 'παιδάριον = boy; οὐκ ἔστιν = is not.'},
      {'key': 'c2', 'prompt': 'Choose the English.', 'greek': 'διέρρηξε τὰ ἱμάτια αὐτοῦ', 'options': ['He tore his garments.', 'He washed his garments.', 'He stripped off his tunic.', 'He put on sackcloth.'], 'answer': 'He tore his garments.', 'yes': 'Yes. διαρρήγνυμι = tear in two; ἱμάτια = garments.', 'no': 'διέρρηξε = tore; ἱμάτια = garments.'},
    ],
    'writes': [
      {'key': 'w1', 'english': 'The boy is not.', 'tiles': ['τὸ', 'παιδάριον', 'οὐκ', 'ἔστιν'], 'target': ['τὸ', 'παιδάριον', 'οὐκ', 'ἔστιν'], 'yes': 'Yes. τὸ παιδάριον οὐκ ἔστιν.', 'no': 'Order: τὸ παιδάριον οὐκ ἔστιν.'},
      {'key': 'w2', 'english': 'He tore his garments.', 'tiles': ['διέρρηξε', 'τὰ', 'ἱμάτια', 'αὐτοῦ'], 'target': ['διέρρηξε', 'τὰ', 'ἱμάτια', 'αὐτοῦ'], 'yes': 'Yes. διέρρηξε τὰ ἱμάτια αὐτοῦ.', 'no': 'Order: διέρρηξε τὰ ἱμάτια αὐτοῦ.'},
    ],
    'practice': [
      {'id': 'p1', 'kind': 'choose', 'ref': 'Gen 37:32', 'greek': 'Τοῦτον εὕρομεν', 'prompt': 'Choose the English.', 'options': ['This we have found.', 'This we have made.', 'This we have torn.', 'This we have bought.'], 'answer': 'This we have found.', 'yes': 'Yes. εὕρομεν is 2nd aorist active of εὑρίσκω (we found).', 'no': 'εὑρίσκω = find; εὕρομεν = we found.'},
      {'id': 'p2', 'kind': 'match', 'ref': 'Gen 37:29–32', 'prompt': 'Match each Greek word to its meaning.', 'pairs': [
        {'id': 'a', 'greek': 'παιδάριον', 'english': 'boy / lad'},
        {'id': 'b', 'greek': 'ἱμάτια', 'english': 'garments'},
        {'id': 'c', 'greek': 'ἔριφον', 'english': 'kid (young goat)'},
        {'id': 'd', 'greek': 'ἐπίγνωθι', 'english': 'recognize!'},
      ], 'yes': 'Yes. All four match.', 'no': 'Check παιδάριον (boy) and ἱμάτια (garments).'},
      {'id': 'p3', 'kind': 'tiles', 'ref': 'Gen 37:30', 'english': '“The boy is not.”', 'prompt': 'Build this Greek clause:', 'tiles': ['τὸ', 'παιδάριον', 'οὐκ', 'ἔστιν'], 'target': ['τὸ', 'παιδάριον', 'οὐκ', 'ἔστιν'], 'yes': 'Yes. τὸ παιδάριον οὐκ ἔστιν.', 'no': 'Order: τὸ παιδάριον οὐκ ἔστιν.'},
    ],
  },
  {
    'id': '8', 'roman': 'VIII', 'verses': 'Gen 37:33–36', 'vnums': [33, 34, 35, 36],
    'title': 'Jacob’s mourning; Joseph brought to Egypt',
    'about': 'Emphatic doubling θηρίον πονηρὸν κατέφαγεν; Future καταβήσομαι εἰς ᾅδου; elliptical genitive',
    'patternHeading': 'Notes on Genesis 37:33–36',
    'patternText': 'Jacob recognizes the tunic, mourns Joseph as dead, and refuses comfort; meanwhile the Midianites sell Joseph in Egypt to Potiphar.',
    'patternRows': [
      ['Χιτὼν τοῦ υἱοῦ μού ἐστιν', 'It is my son’s coat.'],
      ['θηρίον πονηρὸν κατέφαγεν αὐτόν', 'an evil wild beast has devoured him.'],
      ['καταβήσομαι πρὸς τὸν υἱόν μου πενθῶν εἰς ᾅδου', 'I will go down to my son mourning to Hades.'],
    ],
    'rules': [
      {'title': 'Elliptical Genitive (εἰς ᾅδου)', 'rule': 'εἰς ᾅδου (to Hades) is an elliptical genitive with οἶκον (house) understood: into the house of Hades — standard classical and Septuagint Greek.'},
      {'title': 'Deponent Future (καταβήσομαι)', 'rule': 'Many common Greek verbs of motion have middle endings in the future with active meaning: καταβήσομαι (I will go down, from καταβαίνω).'},
      {'title': 'Compound Aorist κατέφαγεν', 'rule': 'κατέφαγεν (devoured, ate up) is the 2nd aorist of κατεσθίω (κατά + ἐσθίω, aorist stem φαγ-): the preposition κατά intensifies the verb to “eat completely / devour.”'},
    ],
    'choices': [
      {'key': 'c1', 'prompt': 'Choose the English.', 'greek': 'θηρίον πονηρὸν κατέφαγεν αὐτόν', 'options': ['An evil wild beast has devoured him.', 'A wild beast fled from him.', 'Evil men have carried him away.', 'He slew an evil wild beast.'], 'answer': 'An evil wild beast has devoured him.', 'yes': 'Yes. θηρίον = wild beast; κατέφαγεν = devoured.', 'no': 'θηρίον = wild beast; πονηρόν = evil; κατέφαγεν = devoured.'},
      {'key': 'c2', 'prompt': 'Choose the English.', 'greek': 'καταβήσομαι πρὸς τὸν υἱόν μου πενθῶν εἰς ᾅδου', 'options': ['I will go down to my son mourning to Hades.', 'My son has gone down into Egypt.', 'I will go up to meet my son in joy.', 'I will mourn for my son in Canaan.'], 'answer': 'I will go down to my son mourning to Hades.', 'yes': 'Yes. καταβήσομαι (will go down) + πενθῶν (mourning) + εἰς ᾅδου (to Hades).', 'no': 'καταβήσομαι = I will go down; πενθῶν = mourning.'},
    ],
    'writes': [
      {'key': 'w1', 'english': 'It is my son’s coat.', 'tiles': ['χιτὼν', 'τοῦ', 'υἱοῦ', 'μού', 'ἐστιν'], 'target': ['χιτὼν', 'τοῦ', 'υἱοῦ', 'μού', 'ἐστιν'], 'yes': 'Yes. χιτὼν τοῦ υἱοῦ μού ἐστιν.', 'no': 'Order: χιτὼν τοῦ υἱοῦ μού ἐστιν.'},
      {'key': 'w2', 'english': 'An evil wild beast has devoured him.', 'tiles': ['θηρίον', 'πονηρὸν', 'κατέφαγεν', 'αὐτόν'], 'target': ['θηρίον', 'πονηρὸν', 'κατέφαγεν', 'αὐτόν'], 'yes': 'Yes. θηρίον πονηρὸν κατέφαγεν αὐτόν.', 'no': 'Order: θηρίον πονηρὸν κατέφαγεν αὐτόν.'},
    ],
    'practice': [
      {'id': 'p1', 'kind': 'choose', 'ref': 'Gen 37:35', 'greek': 'καὶ οὐκ ἤθελε παρακαλεῖσθαι', 'prompt': 'Choose the English.', 'options': ['and he refused to be comforted', 'and he desired to speak with them', 'and he was comforted by his sons', 'and he could not rise up'], 'answer': 'and he refused to be comforted', 'yes': 'Yes. οὐκ ἤθελε (was unwilling) + παρακαλεῖσθαι (pass. inf.: to be comforted).', 'no': 'παρακαλέω = comfort; παρακαλεῖσθαι = to be comforted.'},
      {'id': 'p2', 'kind': 'match', 'ref': 'Gen 37:33–36', 'prompt': 'Match each Greek word to its meaning.', 'pairs': [
        {'id': 'a', 'greek': 'θηρίον', 'english': 'wild beast'},
        {'id': 'b', 'greek': 'πενθῶν', 'english': 'mourning'},
        {'id': 'c', 'greek': 'σάκκον', 'english': 'sackcloth'},
        {'id': 'd', 'greek': 'ᾅδου', 'english': 'Hades'},
      ], 'yes': 'Yes. All four match.', 'no': 'Check θηρίον (wild beast) and πενθῶν (mourning).'},
      {'id': 'p3', 'kind': 'tiles', 'ref': 'Gen 37:33', 'english': '“An evil wild beast has devoured him.”', 'prompt': 'Build this Greek clause:', 'tiles': ['θηρίον', 'πονηρὸν', 'κατέφαγεν', 'αὐτόν'], 'target': ['θηρίον', 'πονηρὸν', 'κατέφαγεν', 'αὐτόν'], 'yes': 'Yes. θηρίον πονηρὸν κατέφαγεν αὐτόν.', 'no': 'Order: θηρίον πονηρὸν κατέφαγεν αὐτόν.'},
    ],
  },
  {
    'id': '9', 'roman': 'IX', 'verses': 'Gen 37:1–36', 'vnums': [1, 3, 5, 8, 11, 20, 27, 33, 35],
    'title': 'Review: Joseph Sold into Egypt',
    'about': 'Septuagint idioms in Genesis 37: periphrastic imperfect, Hebraisms, vivid subjunctive, and narrative verbs',
    'patternHeading': 'Review of Genesis 37',
    'patternText': 'Key Septuagint idioms from Genesis 37: periphrastic imperfects (ἦν ποιμαίνων), prepositional comparisons (παρὰ πάντας / ἐκ πάντων), Hebraistic verb idioms (προσέθεντο ἔτι μισεῖν, βασιλεύων βασιλεύσεις), and classic Greek syntax (ὅπως + subjunctive, εἰς ᾅδου).',
    'patternRows': [
      ['ἦν ποιμαίνων τὰ πρόβατα', 'Periphrastic imperfect: was feeding the sheep.'],
      ['προσέθεντο ἔτι μισεῖν αὐτόν', 'LXX Hebraism: hated him yet the more.'],
      ['καταβήσομαι πενθῶν εἰς ᾅδου', 'Elliptical genitive: go down mourning to Hades.'],
    ],
    'rules': [
      {'title': 'Septuagint Hebraisms', 'rule': 'The LXX frequently reflects Hebrew syntax in Greek dress: παρά/ἐκ for comparison (παρὰ πάντας), participle + finite verb for emphasis (βασιλεύων βασιλεύσεις), and προστίθημι + infinitive for “again / still more” (προσέθεντο ἔτι μισεῖν).'},
      {'title': 'Analytic Imperfect & Imperatives', 'rule': 'ἦν + present participle (ἦν ποιμαίνων) serves as an analytic imperfect; 3rd plural imperatives regularly end in -ωσαν (ἔστωσαν).'},
      {'title': 'Classical Constructions Retained', 'rule': 'Alongside Hebraisms, the Pentateuch preserves idiomatic Greek: genitive after ἀκούω, elliptical εἰς ᾅδου, vivid subjunctive ὅπως ἐξέληται, and deponent futures (καταβήσομαι).'},
    ],
    'choices': [
      {'key': 'c1', 'prompt': 'Choose the English.', 'greek': 'προσέθεντο ἔτι μισεῖν αὐτόν', 'options': ['They hated him yet the more.', 'They cast him into the pit.', 'They sold him to the merchants.', 'They tore their garments.'], 'answer': 'They hated him yet the more.', 'yes': 'Yes. προσέθεντο ἔτι + infinitive = still more.', 'no': 'προσέθεντο ἔτι μισεῖν = hated him still more.'},
      {'key': 'c2', 'prompt': 'Choose the English.', 'greek': 'θηρίον πονηρὸν κατέφαγεν αὐτόν', 'options': ['An evil wild beast has devoured him.', 'His father kept the saying.', 'He was feeding his father’s sheep.', 'The pit was empty and had no water.'], 'answer': 'An evil wild beast has devoured him.', 'yes': 'Yes. θηρίον πονηρὸν κατέφαγεν αὐτόν.', 'no': 'θηρίον = wild beast; κατέφαγεν = devoured.'},
    ],
    'writes': [
      {'key': 'w1', 'english': 'His father kept the saying.', 'tiles': ['ὁ', 'πατὴρ', 'αὐτοῦ', 'διετήρησε', 'τὸ', 'ῥῆμα'], 'target': ['ὁ', 'πατὴρ', 'αὐτοῦ', 'διετήρησε', 'τὸ', 'ῥῆμα'], 'yes': 'Yes. ὁ πατὴρ αὐτοῦ διετήρησε τὸ ῥῆμα.', 'no': 'Order: ὁ πατὴρ αὐτοῦ διετήρησε τὸ ῥῆμα.'},
      {'key': 'w2', 'english': 'Do not shed blood.', 'tiles': ['μὴ', 'ἐκχέητε', 'αἷμα'], 'target': ['μὴ', 'ἐκχέητε', 'αἷμα'], 'yes': 'Yes. μὴ ἐκχέητε αἷμα.', 'no': 'Order: μὴ ἐκχέητε αἷμα.'},
    ],
    'practice': [
      {'id': 'p1', 'kind': 'choose', 'ref': 'Gen 37:2', 'greek': 'ἦν ποιμαίνων τὰ πρόβατα', 'prompt': 'Choose the English.', 'options': ['he was shepherding the sheep', 'he sold the sheep', 'he sought his brothers', 'he dreamed a dream'], 'answer': 'he was shepherding the sheep', 'yes': 'Yes. Analytic imperfect: ἦν ποιμαίνων.', 'no': 'ἦν + ποιμαίνων = was shepherding.'},
      {'id': 'p2', 'kind': 'choose', 'ref': 'Gen 37:27', 'greek': 'ἤκουσαν δὲ οἱ ἀδελφοὶ αὐτοῦ', 'prompt': 'Choose the English.', 'options': ['and his brothers obeyed', 'and his brothers hated him', 'and his brothers departed', 'and his brothers wept'], 'answer': 'and his brothers obeyed', 'yes': 'Yes. ἤκουσαν here means hearkened / obeyed.', 'no': 'ἀκούω in the LXX frequently means obey/hearken.'},
      {'id': 'p3', 'kind': 'tiles', 'ref': 'Gen 37:35', 'english': '“I will go down to my son mourning to Hades.”', 'prompt': 'Build this Greek clause:', 'tiles': ['καταβήσομαι', 'πρὸς', 'τὸν', 'υἱόν', 'μου', 'πενθῶν', 'εἰς', 'ᾅδου'], 'target': ['καταβήσομαι', 'πρὸς', 'τὸν', 'υἱόν', 'μου', 'πενθῶν', 'εἰς', 'ᾅδου'], 'yes': 'Yes. καταβήσομαι πρὸς τὸν υἱόν μου πενθῶν εἰς ᾅδου.', 'no': 'Order: καταβήσομαι πρὸς τὸν υἱόν μου πενθῶν εἰς ᾅδου.'},
    ],
  },
]

# Full roadmap of all 7 narratives in Conybeare & Stock (1905)
ROADMAP_LOCKED = [
  {'lesson': 'X',   'verses': 'Gen 39–45',   'about': 'Story of Joseph (cont.): Potiphar, Pharaoh’s dreams, and reconciliation', 'status': 'Locked'},
  {'lesson': 'XI',  'verses': 'Exod 1–3',    'about': 'Story of the Exodus: Moses in Egypt and the burning bush', 'status': 'Locked'},
  {'lesson': 'XII', 'verses': 'Exod 12–15',  'about': 'Story of the Exodus: Passover and crossing the Red Sea', 'status': 'Locked'},
  {'lesson': 'XIII','verses': 'Num 22–24',   'about': 'Story of Balaam: Balak, the speaking donkey, and the oracles', 'status': 'Locked'},
  {'lesson': 'XIV', 'verses': 'Judg 13–16',  'about': 'Story of Samson: birth, riddle, Delilah, and the temple of Dagon', 'status': 'Locked'},
  {'lesson': 'XV',  'verses': '1 Sam 17',    'about': 'Story of David and Goliath: the valley of Elah and the five smooth stones', 'status': 'Locked'},
  {'lesson': 'XVI', 'verses': '1 Kgs 17–19', 'about': 'Story of Elijah: the widow of Zarephath, Mount Carmel, and Horeb', 'status': 'Locked'},
  {'lesson': 'XVII','verses': '2 Kgs 18–19', 'about': 'Hezekiah and Sennacherib: the siege of Jerusalem and deliverance', 'status': 'Locked'},
]

lessons = {}
unit_map = []
all_gp = {}

for spec in LESSONS_SPEC:
    passages, words, gp = build_passages_and_words(gen37, 'Gen', 37, spec['vnums'])
    all_gp.update(gp)
    reread_gk = [' '.join(t['word'] for t in psg['tokens']) for psg in passages]
    reread_en = [gen37[str(vn)][2] for vn in spec['vnums'] if gen37[str(vn)][2]]
    lessons[spec['id']] = {
        'title': spec['title'],
        'verses': spec['verses'],
        'practiceTitle': spec['title'],
        'passages': passages,
        'words': words,
        'patternHeading': spec['patternHeading'],
        'patternText': spec['patternText'],
        'patternRows': spec['patternRows'],
        'rules': spec['rules'],
        'choices': spec['choices'],
        'writes': spec['writes'],
        'rereadGreek': reread_gk,
        'rereadEnglish': reread_en,
        'practice': spec['practice'],
    }
    unit_map.append({'lesson': spec['roman'], 'verses': spec['verses'], 'about': spec['about'], 'status': 'Ready'})

unit_map.extend(ROADMAP_LOCKED)

u1 = json.load(open(os.path.join(W, 'data', 'unit1.json'), encoding='utf-8'))

unit2 = {
    'version': 1,
    'storageKey': 'gallicantus.workbook.septuagint.v1',
    'title': 'Unit 2 · Reading the Septuagint',
    'summary': 'Read the classic narratives of the Greek Old Testament.',
    'lessonSteps': u1['lessonSteps'],
    'eimiSteps': u1['eimiSteps'],
    'lessonQuiz': u1['lessonQuiz'],
    'eimiQuiz': u1['eimiQuiz'],
    'johnLessons': [s['id'] for s in LESSONS_SPEC],
    'unitMap': unit_map,
    'standingCharts': u1['standingCharts'],
    'standingChartTables': u1['standingChartTables'],
    'glossParse': all_gp,
    'lessons': lessons,
    'eimi': u1['eimi'],
    'sources': {
        'text': 'Septuagint text: Brenton (1851, public domain). Notes and grammar observations: F. C. Conybeare & St. George Stock, Selections from the Septuagint (1905, public domain).',
        'links': []
    },
}

out_json = os.path.join(W, 'data', 'unit2.json')
out_js = os.path.join(W, 'js', 'unit2.js')
json.dump(unit2, open(out_json, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
with open(out_js, 'w', encoding='utf-8') as f:
    f.write('window.GALLICANTUS_UNIT2 = ')
    json.dump(unit2, f, ensure_ascii=False, indent=2)
    f.write(';\n')

print('Built Unit 2:', len(lessons), 'ready lessons,', len(unit_map), 'total rows in Contents,', round(os.path.getsize(out_js)/1024, 1), 'KB')

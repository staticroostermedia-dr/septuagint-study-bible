"""PWA step: icons (if missing), offline file list with content hashes, and sw.js with a content-derived cache version.
Read-only on data; safe to run on its own. Run last in run_all.sh."""
import hashlib, json, os
LATIN = os.environ.get('LATIN', '1') == '1'   # Latin layer ships (study-bible-latin); LATIN=0 builds the Greek-only list
BUILD_ONLY = {'en2'}   # LXX2012 full text: build input for data/lx/ only, never fetched by the app
LATIN_PATHS = {'vul', 'vp', 'ls', 'latocc', 'latlex.json', 'latmorph.json', 'latsearch.json', 'vulmap.json'}
HERE = os.path.dirname(os.path.abspath(__file__)); S = os.environ.get('SITE') or os.path.join(HERE, '..', 'site')
ICON = os.path.join(S, 'icons')

def icons():
    from PIL import Image, ImageDraw, ImageFont
    os.makedirs(ICON, exist_ok=True)
    F = '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'
    def make(size, maskable, name):
        p = os.path.join(ICON, name)
        if os.path.exists(p): return
        big = size * 4; im = Image.new('RGB', (big, big), '#14213d'); d = ImageDraw.Draw(im)
        safe = 0.62 if maskable else 0.8          # maskable: keep the mark inside the 80% safe circle
        if not maskable:                          # subtle rounded inner border on the normal icon
            m = int(big * 0.06); d.rounded_rectangle([m, m, big - m, big - m], radius=int(big * 0.14), outline='#c9a24e', width=max(2, big // 90))
        txt = 'ΛΧΧ'; fs = int(big * safe * 0.36); f = ImageFont.truetype(F, fs); gap = fs * 0.12
        bbs = [d.textbbox((0, 0), ch, font=f) for ch in txt]; ws = [b[2] - b[0] for b in bbs]
        w = sum(ws) + gap * (len(txt) - 1); bb = d.textbbox((0, 0), txt, font=f); h = bb[3] - bb[1]
        y = (big - h) / 2 - bb[1] - big * 0.04; x = (big - w) / 2
        for ch, b, cw in zip(txt, bbs, ws): d.text((x - b[0], y), ch, font=f, fill='#e8c36a'); x += cw + gap
        ly = y + bb[3] + big * 0.05; lw = w * 0.55
        d.line([((big - lw) / 2, ly), ((big + lw) / 2, ly)], fill='#c9a24e', width=max(2, big // 70))
        im.resize((size, size), Image.LANCZOS).save(p, optimize=True)
    for s in (192, 512): make(s, False, f'icon-{s}.png'); make(s, True, f'maskable-{s}.png')
    make(180, False, 'apple-touch-icon.png')

def h(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]

icons()
SHELL = ['./', 'index.html', 'about.html', 'app.js', 'style.css', 'manifest.webmanifest', 'fonts/GentiumPlus-Regular.woff2', 'fonts/GentiumPlus-Bold.woff2',
         'icons/icon-192.png', 'icons/icon-512.png', 'icons/maskable-192.png', 'icons/maskable-512.png', 'icons/apple-touch-icon.png',
         'data/books.json', 'data/morph.json', 'data/chapnotes.json', 'data/counts.json', 'data/nt.json', 'data/lexicon.json', 'data/notes.json'] + (['data/vulmap.json'] if LATIN else [])
files = {}; total = 0
for root, _, fs in os.walk(os.path.join(S, 'data')):
    for f in fs:
        if not f.endswith('.json'): continue
        p = os.path.join(root, f); r = os.path.relpath(p, S).replace(os.sep, '/')
        if (not LATIN and r.split('/')[1] in LATIN_PATHS) or r.split('/')[1] in BUILD_ONLY: continue   # Latin layer parked: never offer it offline
        files[r] = [os.path.getsize(p), h(p)]; total += os.path.getsize(p)
shellh = hashlib.sha256(''.join(h(os.path.join(S, x)) for x in SHELL if x != './').encode()).hexdigest()[:10]
datah = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()[:10]
ver = shellh + '-' + datah
json.dump({'version': ver, 'total': total, 'files': files, 'shell': [x for x in SHELL if x in files]}, open(os.path.join(S, 'offline-files.json'), 'w'), separators=(',', ':'), sort_keys=True)
sw = open(os.path.join(HERE, 'sw_template.js'), encoding='utf-8').read().replace('__VERSION__', ver).replace('__SHELL__', json.dumps(SHELL))
open(os.path.join(S, 'sw.js'), 'w', encoding='utf-8').write(sw)
print('pwa: version', ver, 'files', len(files), 'MB', round(total / 1e6, 1))

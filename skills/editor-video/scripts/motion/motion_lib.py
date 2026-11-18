"""Biblioteca de motion editorial para Reels em tela dividida (painel de cima 1080x960).
Estilo aprovado: fundo claro com grade, tipografia cinética palavra a palavra (Inter Bold + Light Itálico),
cartões de interface com sombra, diagramas e gráficos, grifo amarelo, cursor e legenda natural.
Uso: um arquivo de cenas (ver cenas_exemplo.py) faz `from motion_lib import *`, chama `init(...)`
e define a lista SC. render_motion.py renderiza os quadros.
"""
import json, math, os, sys, re
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, '..', '..', 'assets', 'fonts')
INTER = os.path.join(FONTS, 'Inter.ttf')
INTERI = os.path.join(FONTS, 'InterItalic.ttf')
FPS = 30
W = []          # palavras do áudio final: [{w, s, e}]
DUR = 0.0
KEY = set()     # palavras-chave grifadas na legenda
CH = []

def ease(x):
    x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3
def ease_back(x):
    x = max(0.0, min(1.0, x)); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2

BG = (240, 238, 234); INK = (32, 30, 31); GREY = (150, 146, 141); LIGHT = (205, 201, 195)
HL = (225, 254, 82); WHITE = (255, 255, 255); ORANGE = (235, 99, 60); GREEN = (64, 168, 92)
TW, TH = 1080, 960

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def smooth(x): x = clamp(x); return x * x * (3 - 2 * x)
def lerp(a, b, m): return a + (b - a) * m
def lerpc(c1, c2, m): return tuple(int(lerp(a, b, m)) for a, b in zip(c1, c2))

WGT = {'l': 300, 'r': 400, 'm': 500, 's': 600, 'b': 700, 'x': 800}
_fc = {}
def font(size, w=700, italic=False):
    k = (size, w, italic)
    if k not in _fc:
        f = ImageFont.truetype(INTERI if italic else INTER, size)
        vals = []
        for a in f.get_variation_axes():
            n = a['name'] if isinstance(a['name'], str) else a['name'].decode()
            vals.append(min(32, a['maximum']) if 'ptical' in n else w)
        f.set_variation_by_axes(vals)
        _fc[k] = f
    return _fc[k]

def text_img(s, size, w, color, italic=False, track=-0.03):
    f = font(size, w, italic)
    asc, desc = f.getmetrics()
    im = Image.new('RGBA', (int(f.getlength(s) + size) + 40, asc + desc + 40), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((20, 20), s, font=f, fill=color + (255,))
    bb = im.getbbox() or (0, 0, 1, 1)
    return im.crop((bb[0], 0, bb[2] + 2, im.height)), 20 + asc

# ---------- background ----------
_bgc = {}
def background():
    if 'bg' in _bgc: return _bgc['bg']
    S = 2
    im = Image.new('RGBA', (TW * S, TH * S), BG + (255,))
    d = ImageDraw.Draw(im)
    step = 80
    for x in range(0, TW + 1, step):
        d.line((x * S, 0, x * S, TH * S), fill=(232, 229, 224, 255), width=S)
    for y in range(0, TH + 1, step):
        d.line((0, y * S, TW * S, y * S), fill=(232, 229, 224, 255), width=S)
    for x in range(0, TW + 1, step):
        for y in range(0, TH + 1, step):
            d.line(((x - 5) * S, y * S, (x + 5) * S, y * S), fill=(214, 210, 204, 255), width=S)
            d.line((x * S, (y - 5) * S, x * S, (y + 5) * S), fill=(214, 210, 204, 255), width=S)
    im = im.resize((TW, TH), Image.LANCZOS)
    _bgc['bg'] = im
    return im

# ---------- kinetic text lines ----------
# line: (t, y, [(word, style)], size, stagger)
# style chars: b bold ink, l light italic, r regular, m medium, h bold + highlight, o bold orange
_wc = {}
def word_img(word, style, size):
    k = (word, style, size)
    if k in _wc: return _wc[k]
    italic = 'l' in style or 'i' in style
    w = WGT['b'] if style[0] in 'bho' else WGT.get(style[0], 400)
    if style[0] == 'l': w = 300
    color = ORANGE if style[0] == 'o' else INK
    im, base = text_img(word, size, w, color, italic)
    grey, _ = text_img(word, size, w, LIGHT, italic)
    _wc[k] = (im, grey, base)
    return _wc[k]

def word_times(t0, words, stagger):
    return [t0 + i * stagger for i in range(len(words))]

def draw_line(canvas, t, line, alpha_out=1.0):
    t0, y, words, size = line[:4]
    stagger = line[4] if len(line) > 4 else 0.12
    ts = line[5] if len(line) > 5 else word_times(t0, words, stagger)
    if t < ts[0] - 0.01: return
    imgs = [word_img(w, s, size) for w, s in words]
    sp = size * 0.24
    # revealed width for re-centering
    rw = 0.0
    for i, (im, g, b) in enumerate(imgs):
        q = smooth((t - ts[i]) / 0.3)
        rw += (im.width + (sp if i else 0)) * q
    x = TW / 2 - rw / 2
    for i, ((im, grey, base), (w, s)) in enumerate(zip(imgs, words)):
        p = (t - ts[i]) / 0.38
        if p <= 0: break
        a = smooth(p)
        img = Image.blend(grey, im, smooth((t - ts[i]) / 0.5)) if p < 1.4 else im
        if a < 1:
            img = img.filter(ImageFilter.GaussianBlur(7 * (1 - a)))
            img.putalpha(img.getchannel('A').point(lambda v: int(v * a)))
        if alpha_out < 1:
            img = img.copy(); img.putalpha(img.getchannel('A').point(lambda v: int(v * alpha_out)))
        xx = x + 26 * (1 - a)
        yy = y - base
        if s[0] == 'h':
            q = smooth((t - ts[i] - 0.15) / 0.3)
            if q > 0:
                hl = Image.new('RGBA', (int(im.width * q) + 16, int(size * 0.78)), HL + (int(255 * alpha_out),))
                canvas.alpha_composite(hl, (int(xx - 8), int(y - size * 0.66)))
        canvas.alpha_composite(img, (int(xx), int(yy)))
        x += im.width + sp

# ---------- cards ----------
S2 = 2
def card_base(w, h, title=None, dots=True):
    im = Image.new('RGBA', (w * S2, h * S2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w * S2 - 1, h * S2 - 1), 18 * S2, fill=WHITE + (255,), outline=(226, 222, 216, 255), width=S2)
    if dots:
        for k in range(3):
            d.ellipse(((24 + k * 22) * S2, 20 * S2, (36 + k * 22) * S2, 32 * S2), fill=(222, 218, 212, 255))
    if title:
        d.text((w * S2 / 2, 26 * S2), title, font=font(18 * S2, 500), fill=GREY + (255,), anchor='mm')
        d.line((0, 50 * S2, w * S2, 50 * S2), fill=(236, 232, 227, 255), width=S2)
    return im, d

def finish_card(im):
    w, h = im.width // S2, im.height // S2
    return im.resize((w, h), Image.LANCZOS)

def place_card(canvas, card, cx, cy, t, t0, tilt=0.0):
    p = clamp((t - t0) / 0.5)
    if p <= 0: return
    e = ease_back(p) if p < 1 else 1
    sc = 0.9 + 0.1 * e
    float_y = 5 * math.sin((t - t0) * 1.6)
    ang = tilt + 1.2 * math.sin((t - t0) * 0.9)
    c = card.resize((int(card.width * sc), int(card.height * sc)), Image.BICUBIC).rotate(ang, resample=Image.BICUBIC, expand=True)
    pad = 60
    sh = Image.new('RGBA', (c.width + pad * 2, c.height + pad * 2), (0, 0, 0, 0))
    a = c.getchannel('A').point(lambda v: int(v * 0.16 * smooth(p)))
    s1 = Image.new('RGBA', c.size, (40, 32, 28, 0)); s1.putalpha(a)
    sh.paste(s1, (pad, pad + 24))
    sh = sh.filter(ImageFilter.GaussianBlur(26))
    if p < 1:
        c.putalpha(c.getchannel('A').point(lambda v: int(v * smooth(p * 1.4))))
    y = cy + 40 * (1 - smooth(p)) + float_y
    canvas.alpha_composite(sh, (int(cx - c.width / 2 - pad), int(y - c.height / 2 - pad)))
    canvas.alpha_composite(c, (int(cx - c.width / 2), int(y - c.height / 2)))

def typed(s, t, t0, cps=30):
    n = int(clamp((t - t0) * cps, 0, len(s)))
    return s[:n]

def T(d, xy, s, size, w=400, color=INK, italic=False, anchor='la'):
    d.text((xy[0] * S2, xy[1] * S2), s, font=font(size * S2, w, italic), fill=color + (255,), anchor=anchor)

def hl_rect(d, x, y, w, h, q):
    if q <= 0: return
    d.rounded_rectangle((x * S2, y * S2, (x + w * q) * S2, (y + h) * S2), 4 * S2, fill=HL + (255,))

def card_chat(t, cfg):
    w, h = 760, 400
    im, d = card_base(w, h, 'Agente de tráfego')
    msg = cfg['user']
    s = typed(msg, t, cfg['t_user'], 34)
    if s:
        f = font(24 * S2, 500)
        tw = min(560, f.getlength(msg) / S2 + 40)
        x1 = w - 30; x0 = x1 - tw
        d.rounded_rectangle((x0 * S2, 76 * S2, x1 * S2, 128 * S2), 26 * S2, fill=(241, 238, 233, 255))
        T(d, (x0 + 20, 102), s, 24, 500, INK, anchor='lm')
    if 't_conn' in cfg and t >= cfg['t_conn']:
        q = smooth((t - cfg['t_conn']) / 0.35)
        y = 160
        d.rounded_rectangle((30 * S2, y * S2, (w - 30) * S2, (y + 74) * S2), 14 * S2, outline=(226, 222, 216, int(255 * q)), width=2 * S2)
        d.rounded_rectangle((50 * S2, (y + 17) * S2, 90 * S2, (y + 57) * S2), 10 * S2, fill=INK + (int(255 * q),))
        T(d, (70, y + 37), 'M', 22, 700, WHITE, anchor='mm')
        T(d, (108, y + 26), 'Meta Ads', 24, 700, lerpc(WHITE, INK, q), anchor='lm')
        T(d, (108, y + 52), 'MCP oficial', 18, 400, lerpc(WHITE, GREY, q), anchor='lm')
        if t >= cfg.get('t_ok', 1e9):
            q2 = smooth((t - cfg['t_ok']) / 0.3)
            d.ellipse(((w - 190) * S2, (y + 31) * S2, (w - 178) * S2, (y + 43) * S2), fill=GREEN + (int(255 * q2),))
            T(d, (w - 168, y + 37), 'Conectado', 20, 600, lerpc(WHITE, INK, q2), anchor='lm')
        else:
            T(d, (w - 50, y + 37), 'Conectar', 20, 600, lerpc(WHITE, GREY, q), anchor='rm')
    if 'chips' in cfg:
        x = 30; y = 270
        for lab, tc in cfg['chips']:
            if t < tc: continue
            q = smooth((t - tc) / 0.3)
            f = font(20 * S2, 500); cw = f.getlength(lab) / S2 + 36
            if x + cw > w - 30: x = 30; y += 54
            d.rounded_rectangle((x * S2, y * S2, (x + cw) * S2, (y + 40) * S2), 20 * S2, fill=lerpc(WHITE, (241, 238, 233), q) + (255,))
            T(d, (x + cw / 2, y + 20), lab, 20, 500, lerpc(WHITE, INK, q), anchor='mm')
            x += cw + 12
    return finish_card(im)

def card_reply(t, cfg):
    w, h = 760, 380
    im, d = card_base(w, h, 'Agente de tráfego')
    d.rounded_rectangle(((w - 380) * S2, 76 * S2, (w - 30) * S2, 128 * S2), 26 * S2, fill=(241, 238, 233, 255))
    T(d, (w - 360, 102), 'Analisa minhas campanhas', 22, 500, INK, anchor='lm')
    if t >= cfg['t_r']:
        n = int(clamp((t - cfg['t_r']) * 9, 0, 6))
        widths = [640, 580, 610, 420, 600, 360]
        for k in range(n):
            d.rounded_rectangle((30 * S2, (160 + k * 30) * S2, (30 + widths[k]) * S2, (174 + k * 30) * S2), 7 * S2, fill=(232, 229, 224, 255))
    if t >= cfg['t_tag']:
        q = smooth((t - cfg['t_tag']) / 0.3)
        T(d, (30, 352), 'resposta genérica', 22, 300, lerpc(WHITE, GREY, q), italic=True, anchor='lm')
    if t >= cfg['t_db']:
        q = smooth((t - cfg['t_db']) / 0.3)
        d.rounded_rectangle(((w - 290) * S2, 334 * S2, (w - 30) * S2, 370 * S2), 18 * S2, fill=lerpc(WHITE, (253, 236, 230), q) + (255,))
        T(d, (w - 160, 352), 'sem base de dados', 19, 600, lerpc(WHITE, ORANGE, q), anchor='mm')
    return finish_card(im)

def card_files(t, cfg):
    out = []
    for name, tf in cfg['files']:
        w, h = 230, 150
        im, d = card_base(w, h, None, dots=False)
        d.rounded_rectangle((24 * S2, 26 * S2, 64 * S2, 74 * S2), 6 * S2, fill=(236, 232, 227, 255))
        T(d, (24, 112), name, 21, 600, INK, anchor='lm')
        if t >= cfg['t_x']:
            q = smooth((t - cfg['t_x']) / 0.3)
            d.line((14 * S2, 75 * S2, (14 + (w - 28) * q) * S2, 75 * S2), fill=ORANGE + (255,), width=4 * S2)
        out.append((finish_card(im), tf))
    return out

def card_tree(t, cfg):
    w, h = 700, 430
    im, d = card_base(w, h, 'estrutura-de-analise.md')
    rows = cfg['rows']
    cur = max([i for i, (_, tr) in enumerate(rows) if t >= tr] or [-1])
    for i, (lab, tr) in enumerate(rows):
        if t < tr: continue
        q = smooth((t - tr) / 0.3)
        x = 40 + i * 44; y = 92 + i * 66
        if i:
            d.line(((x - 26) * S2, (y - 40) * S2, (x - 26) * S2, (y) * S2), fill=(214, 210, 204, 255), width=2 * S2)
            d.line(((x - 26) * S2, y * S2, (x - 8) * S2, y * S2), fill=(214, 210, 204, 255), width=2 * S2)
        f = font(28 * S2, 600 if i == cur else 400)
        tw = f.getlength(lab) / S2
        if i == cur: hl_rect(d, x - 6, y - 18, tw + 12, 36, smooth((t - tr - 0.1) / 0.3))
        T(d, (x, y), lab, 28, 600 if i == cur else 400, lerpc(WHITE, INK if i == cur else (110, 106, 102), q), anchor='lm')
    return finish_card(im)

def card_log(t, cfg):
    w, h = 780, 440
    im, d = card_base(w, h, 'registro-de-alteracoes.md')
    T(d, (34, 88), '# Registro', 30, 700, INK, anchor='lm')
    rows = cfg['rows']
    cur = max([i for i, (_, _, tr) in enumerate(rows) if t >= tr] or [-1])
    for i, (tag, txt, tr) in enumerate(rows):
        if t < tr: continue
        q = smooth((t - tr) / 0.3)
        y = 160 + i * 92
        f = font(22 * S2, 700); tw = f.getlength(tag) / S2
        if i == cur: hl_rect(d, 30, y - 16, tw + 10, 32, smooth((t - tr - 0.1) / 0.3))
        T(d, (35, y), tag, 22, 700, lerpc(WHITE, INK, q), anchor='lm')
        T(d, (35, y + 34), typed(txt, t, tr, 40), 22, 400, lerpc(WHITE, (100, 96, 92), q), anchor='lm')
    return finish_card(im)

def card_doc(title, heading, lines, hl_from=None, t=0, w=520, h=560):
    im, d = card_base(w, h, title)
    T(d, (34, 92), heading, 30, 700, INK, anchor='lm')
    for k, ln in enumerate(lines):
        y = 150 + k * 40
        d.rounded_rectangle((34 * S2, y * S2, (34 + ln) * S2, (y + 14) * S2), 7 * S2, fill=(232, 229, 224, 255))
    if hl_from is not None and t >= hl_from:
        q = smooth((t - hl_from) / 0.4)
        hl_rect(d, 30, 144, 330, 26, q)
        if t >= hl_from + 0.4: hl_rect(d, 30, 184, 250, 26, smooth((t - hl_from - 0.4) / 0.4))
    return finish_card(im)

def star_img(size, color=INK):
    S = 4; r = size * S / 2
    im = Image.new('RGBA', (int(size * S), int(size * S)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im); c = r
    pts = []
    for k in range(8):
        ang = math.pi / 4 * k - math.pi / 2
        rr = r if k % 2 == 0 else r * 0.28
        pts.append((c + rr * math.cos(ang), c + rr * math.sin(ang)))
    d.polygon(pts, fill=color + (255,))
    return im.resize((int(size), int(size)), Image.LANCZOS)

def draw_bullets(canvas, t, items, x0, y0, size=40, gap=70):
    star = star_img(size * 0.62)
    for i, (txt, ti, st) in enumerate(items):
        p = (t - ti) / 0.35
        if p <= 0: continue
        a = smooth(p)
        y = y0 + i * gap  # baseline
        im, base = text_img(txt, size, WGT['b'] if st in 'bh' else 400, INK)
        lay = Image.new('RGBA', (TW, int(size * 2.2)), (0, 0, 0, 0))
        by = int(size * 1.4)  # baseline inside layer
        if st == 'h':
            q = smooth((t - ti - 0.15) / 0.3)
            if q > 0:
                lay.alpha_composite(Image.new('RGBA', (int((im.width + 16) * q) + 1, int(size * 0.82)), HL + (255,)), (x0 + 52, int(by - size * 0.7)))
        lay.alpha_composite(star, (x0, int(by - size * 0.36 - star.height / 2)))
        lay.alpha_composite(im, (x0 + 60, by - base))
        if a < 1:
            lay = lay.filter(ImageFilter.GaussianBlur(5 * (1 - a)))
            lay.putalpha(lay.getchannel('A').point(lambda v: int(v * a)))
        canvas.alpha_composite(lay, (int(22 * (1 - a)), int(y - by)))

def draw_bar(canvas, t, t0):
    p = smooth((t - t0) / 0.8)
    if t < t0 - 0.2: return
    d = ImageDraw.Draw(canvas)
    x0, x1, y = 160, 920, 640
    d.rounded_rectangle((x0, y - 7, x1, y + 7), 7, fill=(222, 218, 212, 255))
    if p > 0:
        d.rounded_rectangle((x0, y - 7, x0 + max(14, (x1 - x0) * 0.2 * p), y + 7), 7, fill=INK + (255,))

# ---------- scenes ----------
def L(t, y, spec, size, stagger=0.12, times=None):
    words = []
    for tok in spec.split(' '):
        if '|' in tok: w, s = tok.split('|')
        else: w, s = tok, 'r'
        words.append((w.replace('_', ' '), s))
    return (t, y, words, size, stagger) + ((times,) if times else ())


def render_top(SC, t):
    frame = background().copy()
    idx = max(i for i, s in enumerate(SC) if s['s'] <= t)
    sc = SC[idx]
    canvas = Image.new('RGBA', (TW, TH), (0, 0, 0, 0))
    out = 1 - smooth((t - (sc['e'] - 0.18)) / 0.18) if sc['e'] < DUR else 1
    if 'draw' in sc: sc['draw'](canvas, t)
    for ln in sc['lines']:
        draw_line(canvas, t, ln)
    if out < 1:
        canvas = canvas.filter(ImageFilter.GaussianBlur(6 * (1 - out)))
        canvas.putalpha(canvas.getchannel('A').point(lambda v: int(v * out)))
    life = clamp((t - sc['s']) / max(1.0, sc['e'] - sc['s']))
    z = 1.0 + 0.03 * life
    if z > 1.0005:
        cw, ch = int(TW * z), int(TH * z)
        canvas = canvas.resize((cw, ch), Image.BICUBIC).crop(((cw - TW) // 2, (ch - TH) // 2, (cw - TW) // 2 + TW, (ch - TH) // 2 + TH))
    frame.alpha_composite(canvas)
    return frame

def finalize_scenes(SC):
    """Preenche o fim de cada cena com o início da próxima."""
    for i in range(len(SC)):
        SC[i]['e'] = SC[i + 1]['s'] if i + 1 < len(SC) else DUR + 1
    return SC

# ---------- legenda natural: Inter, grifo amarelo na palavra-chave ----------
def norm(w): return re.sub(r'[^\wáàâãéêíóôõúç%]', '', w.lower())
def build_chunks():
    ch = []; cur = []
    for i, w in enumerate(W):
        cur.append(w)
        txt = ' '.join(x['w'] for x in cur)
        nxt = W[i + 1] if i + 1 < len(W) else None
        if (w['w'][-1] in '.,?!:' or len(cur) >= 5 or nxt is None or nxt['s'] - w['e'] > 0.35
                or len(txt) + 1 + len(nxt['w']) > 30):
            ch.append(cur); cur = []
    out = []
    for k, c in enumerate(ch):
        s = c[0]['s']; e = c[-1]['e']
        nxt = ch[k + 1][0]['s'] if k + 1 < len(ch) else e + 0.6
        e = nxt if nxt - e < 0.45 else e + 0.25
        words = [x['w'].rstrip('.,?!') or x['w'] for x in c]
        keys = [j for j, x in enumerate(words) if norm(x) in KEY and not x.isupper()]
        out.append({'s': s, 'e': e, 'words': words, 'keys': keys[-1:] if keys else [], 'ws': [x['s'] for x in c]})
    return out
CAP_Y = 905
CAP_SIZE = 40

def init(palavras_json, dur, keywords):
    """palavras_json: saída de palavras.py; dur: duração do vídeo final (s); keywords: set de palavras grifáveis."""
    global W, DUR, KEY, CH
    W = json.load(open(palavras_json)); DUR = dur; KEY = set(k.lower() for k in keywords)
    CH = build_chunks()

def kw(sub, after=0.0, default=None):
    """Tempo (s) da primeira palavra que contém `sub` depois de `after`."""
    for w in W:
        if w['s'] >= after - 0.01 and sub.lower() in w['w'].lower():
            return w['s']
    return default if default is not None else after

def caption_layer(t, lay):
    for c in CH:
        if not (c['s'] - 0.02 <= t < c['e']): continue
        f = font(CAP_SIZE, 500)
        imgs = [text_img(w, CAP_SIZE, 600 if j in c['keys'] else 500, INK, False, -0.01) for j, w in enumerate(c['words'])]
        sp = CAP_SIZE * 0.28
        total = sum(im.width for im, _ in imgs) + sp * (len(imgs) - 1)
        x = TW / 2 - total / 2
        for j, (im, base) in enumerate(imgs):
            p = smooth((t - c['ws'][j] + 0.04) / 0.14)
            if p > 0:
                if j in c['keys']:
                    q = smooth((t - c['ws'][j] - 0.05) / 0.25)
                    hl = Image.new('RGBA', (int((im.width + 14) * q) + 1, int(CAP_SIZE * 0.82)), HL + (255,))
                    lay.alpha_composite(hl, (int(x - 7), int(CAP_Y - CAP_SIZE * 0.7)))
                img = im if p >= 1 else im.copy()
                if p < 1: img.putalpha(im.getchannel('A').point(lambda v: int(v * p)))
                lay.alpha_composite(img, (int(x), int(CAP_Y - base + 4 * (1 - p))))
            x += im.width + sp
        break

# ---------- primitivas de cena ----------
def emoji_img(e, size, grey=False):
    k = (e, size, grey)
    if k in _ei: return _ei[k]
    f = ImageFont.truetype(EMOJI, 160)
    im = Image.new('RGBA', (240, 240), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((20, 20), e, font=f, embedded_color=True)
    im = im.crop(im.getbbox())
    s = size / max(im.size)
    im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    if grey:
        a = im.getchannel('A')
        g = ImageOps.grayscale(im.convert('RGB'))
        g = ImageOps.autocontrast(g, cutoff=1).point(lambda v: int(70 + v * 0.72))
        im = Image.merge('RGBA', (g, g, g, a))
    _ei[k] = im
    return im

def float_emoji(canvas, e, x, y, size, t, t0, grey=False, amp=8, rot=4):
    p = (t - t0) / 0.45
    if p <= 0: return
    im = emoji_img(e, size, grey)
    sc = 0.5 + 0.5 * ease_back(clamp(p))
    ang = -12 * (1 - ease(clamp(p))) + rot * math.sin((t - t0) * 1.3)
    im2 = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.BICUBIC).rotate(ang, resample=Image.BICUBIC, expand=True)
    if p < 1: im2.putalpha(im2.getchannel('A').point(lambda v: int(v * smooth(p * 1.5))))
    pad = 40
    sh = Image.new('RGBA', (im2.width + pad * 2, im2.height + pad * 2), (0, 0, 0, 0))
    a = im2.getchannel('A').point(lambda v: int(v * 0.22))
    s1 = Image.new('RGBA', im2.size, (40, 32, 28, 0)); s1.putalpha(a)
    sh.paste(s1, (pad, pad + 18)); sh = sh.filter(ImageFilter.GaussianBlur(16))
    yy = y + amp * math.sin((t - t0) * 1.7)
    canvas.alpha_composite(sh, (int(x - im2.width / 2 - pad), int(yy - im2.height / 2 - pad)))
    canvas.alpha_composite(im2, (int(x - im2.width / 2), int(yy - im2.height / 2)))

def cursor(canvas, t, path, click_ts=()):
    """path: list of (time, x, y). Cursor eases between points."""
    if t < path[0][0] or t > path[-1][0] + 1.2: return
    x, y = path[0][1], path[0][2]
    for (ta, xa, ya), (tb, xb, yb) in zip(path, path[1:]):
        if ta <= t <= tb:
            m = smooth((t - ta) / max(0.01, tb - ta)); x, y = lerp(xa, xb, m), lerp(ya, yb, m)
        elif t > tb: x, y = xb, yb
    a = smooth((t - path[0][0]) / 0.2) * (1 - smooth((t - path[-1][0] - 0.9) / 0.3))
    sc = 1.0
    for ct in click_ts:
        if ct <= t < ct + 0.25: sc = 1 - 0.18 * math.sin((t - ct) / 0.25 * math.pi)
        if ct <= t < ct + 0.5:
            q = (t - ct) / 0.5
            d = ImageDraw.Draw(canvas); r = 10 + 34 * q
            d.ellipse((x - r, y - r, x + r, y + r), outline=INK + (int(150 * (1 - q)),), width=3)
    S = 4; L = 34 * sc
    im = Image.new('RGBA', (int(L * S * 1.2), int(L * S * 1.3)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pts = [(0, 0), (0, L * 0.92), (L * 0.26, L * 0.70), (L * 0.44, L * 1.08), (L * 0.58, L * 1.02), (L * 0.41, L * 0.65), (L * 0.72, L * 0.65)]
    pts = [(px * S + 6, py * S + 6) for px, py in pts]
    d.polygon(pts, fill=INK + (255,), outline=WHITE + (255,))
    d.line(pts + [pts[0]], fill=WHITE + (255,), width=S * 2)
    im = im.resize((im.width // S, im.height // S), Image.LANCZOS)
    im.putalpha(im.getchannel('A').point(lambda v: int(v * a)))
    canvas.alpha_composite(im, (int(x - 2), int(y - 2)))

def spinner(canvas, x, y, t, t0, t1, r=18, color=ORANGE):
    if not (t0 <= t < t1): return
    d = ImageDraw.Draw(canvas)
    a0 = (t - t0) * 420
    d.arc((x - r, y - r, x + r, y + r), a0, a0 + 260, fill=color + (255,), width=5)

def curve(canvas, p0, p1, t, t0, dur=0.5, color=(205, 201, 195), width=3, bend=0.35):
    q = smooth((t - t0) / dur)
    if q <= 0: return
    (x0, y0), (x1, y1) = p0, p1
    cx, cy = (x0 + x1) / 2 - (y1 - y0) * bend, (y0 + y1) / 2 + (x1 - x0) * bend
    pts = []
    n = 40
    for k in range(int(n * q) + 1):
        u = k / n
        pts.append(((1 - u) ** 2 * x0 + 2 * (1 - u) * u * cx + u * u * x1, (1 - u) ** 2 * y0 + 2 * (1 - u) * u * cy + u * u * y1))
    if len(pts) > 1:
        ImageDraw.Draw(canvas).line(pts, fill=color + (255,), width=width, joint='curve')
    if q >= 1:
        ImageDraw.Draw(canvas).ellipse((x1 - 6, y1 - 6, x1 + 6, y1 + 6), fill=color + (255,))

def mini_card(canvas, t, t0, cx, cy, title, kind, w=240, h=170, tilt=0):
    im, d = card_base(w, h, None, dots=False)
    T(d, (20, 28), title, 20, 600, INK, anchor='lm')
    if kind == 'bars':
        vals = [0.35, 0.5, 0.42, 0.7, 0.62, 0.9]
        for k, v in enumerate(vals):
            q = smooth((t - t0 - 0.2 - k * 0.07) / 0.3)
            bh = 90 * v * q; x = 22 + k * 34
            d.rounded_rectangle((x * S2, (h - 22 - bh) * S2, (x + 22) * S2, (h - 22) * S2), 5 * S2, fill=(INK if k == 5 else (214, 210, 204)) + (255,))
    elif kind == 'line':
        q = smooth((t - t0 - 0.2) / 0.9)
        pts = []
        for k in range(int(30 * q) + 1):
            u = k / 30
            pts.append(((20 + u * (w - 40)) * S2, (h - 26 - (u ** 1.7) * 100 - 6 * math.sin(u * 9)) * S2))
        if len(pts) > 1: d.line(pts, fill=INK + (255,), width=4 * S2, joint='curve')
    elif kind == 'lines':
        for k in range(4):
            q = smooth((t - t0 - 0.15 - k * 0.08) / 0.3)
            d.rounded_rectangle((20 * S2, (60 + k * 26) * S2, (20 + (w - 60 - k * 18) * q) * S2, (72 + k * 26) * S2), 6 * S2, fill=(226, 222, 216, 255))
    place_card(canvas, finish_card(im), cx, cy, t, t0, tilt)

def modal_auth(t, t0, t_click):
    w, h = 400, 250
    im, d = card_base(w, h, None, dots=False)
    T(d, (w / 2, 50), 'Permitir acesso?', 26, 700, INK, anchor='mm')
    T(d, (w / 2, 92), 'Meta Ads · leitura de dados', 19, 400, GREY, anchor='mm')
    clicked = t >= t_click
    q = smooth((t - t_click) / 0.25)
    d.rounded_rectangle((40 * S2, 150 * S2, (w - 40) * S2, 206 * S2), 28 * S2, fill=lerpc(INK, GREEN, q) + (255,))
    T(d, (w / 2, 178), 'Autorizado ✓' if clicked else 'Autorizar', 22, 700, WHITE, anchor='mm')
    return finish_card(im)

def comment_box(t, t0, t_type, t_send):
    w, h = 820, 120
    im, d = card_base(w, h, None, dots=False)
    d.ellipse((24 * S2, 32 * S2, 80 * S2, 88 * S2), fill=(226, 222, 216, 255))
    s = typed('PROMPT', t, t_type, 14)
    if s:
        T(d, (104, 60), s, 32, 700, INK, anchor='lm')
        if int(t * 2.5) % 2 == 0 and len(s) < 6:
            fw = font(32 * S2, 700).getlength(s) / S2
            d.line(((106 + fw) * S2, 42 * S2, (106 + fw) * S2, 78 * S2), fill=INK + (255,), width=2 * S2)
    else:
        T(d, (104, 60), 'Adicione um comentário…', 26, 400, GREY, anchor='lm')
    q = smooth((t - t_send) / 0.25)
    d.rounded_rectangle(((w - 150) * S2, 32 * S2, (w - 24) * S2, 88 * S2), 28 * S2, fill=lerpc((226, 222, 216), INK, smooth((t - t_type - 0.4) / 0.3)) + (255,))
    T(d, (w - 87, 60), 'Enviado' if t >= t_send else 'Enviar', 22, 700, WHITE, anchor='mm')
    return finish_card(im)

def months(canvas, t, t0, t1, cx, cy):
    d = ImageDraw.Draw(canvas)
    for k in range(12):
        x = cx - 5.5 * 46 + k * 46
        q = smooth((t - (t0 + (t1 - t0) * k / 12)) / 0.2)
        d.ellipse((x - 14, cy - 14, x + 14, cy + 14), outline=(205, 201, 195, 255), width=3)
        if q > 0:
            r = 14 * q
            d.ellipse((x - r, cy - r, x + r, cy + r), fill=(INK if k < 11 else ORANGE) + (255,))

def timeline(canvas, t, t0, cx, cy, labels):
    d = ImageDraw.Draw(canvas)
    q = smooth((t - t0) / 0.8)
    x0, x1 = cx - 330, cx + 330
    d.line((x0, cy, x0 + (x1 - x0) * q, cy), fill=(205, 201, 195, 255), width=3)
    for k, lab in enumerate(labels):
        x = x0 + k * (x1 - x0) / (len(labels) - 1)
        p = smooth((t - t0 - 0.2 - k * 0.25) / 0.3)
        if p <= 0: continue
        r = 11 * p
        d.ellipse((x - r, cy - r, x + r, cy + r), fill=(INK if k < len(labels) - 1 else ORANGE) + (255,))
        im, base = text_img(lab, 26, 500, INK)
        im.putalpha(im.getchannel('A').point(lambda v: int(v * p)))
        canvas.alpha_composite(im, (int(x - im.width / 2), int(cy + 26)))

# ---------- scene drawing (replaces render3 draws) ----------
# ---------- diagram primitives ----------
def donut(canvas, t, t0, cx, cy, r, parts, width=34, label=None, sub=None):
    """parts: list of (fraction, color, t_start)."""
    S = 2
    im = Image.new('RGBA', (int(r * 2 + width * 2) * S, int(r * 2 + width * 2) * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im); o = width * S
    box = (o, o, o + 2 * r * S, o + 2 * r * S)
    pa = smooth((t - t0) / 0.4)
    if pa <= 0: return
    d.arc(box, 0, 360, fill=(226, 222, 216, int(255 * pa)), width=width * S)
    a = -90
    for frac, col, ts in parts:
        q = smooth((t - ts) / 0.8)
        if q > 0:
            d.arc(box, a, a + 360 * frac * q, fill=col + (255,), width=width * S)
        a += 360 * frac
    im = im.resize((im.width // S, im.height // S), Image.LANCZOS)
    canvas.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))
    if label:
        li, lb = text_img(label, 54, 700, INK); li.putalpha(li.getchannel('A').point(lambda v: int(v * pa)))
        canvas.alpha_composite(li, (int(cx - li.width / 2), int(cy - lb + 14)))
    if sub:
        si, sb = text_img(sub, 22, 400, GREY, True); si.putalpha(si.getchannel('A').point(lambda v: int(v * pa)))
        canvas.alpha_composite(si, (int(cx - si.width / 2), int(cy + 26)))

def node(canvas, t, t0, cx, cy, label, dark=False, w=None, h=64, size=26):
    p = clamp((t - t0) / 0.4)
    if p <= 0: return
    f = font(size * S2, 600)
    w = w or int(f.getlength(label) / S2 + 56)
    im = Image.new('RGBA', (w * S2, h * S2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w * S2 - 1, h * S2 - 1), h * S2 // 2, fill=(INK if dark else WHITE) + (255,), outline=(220, 216, 210, 255), width=S2)
    T(d, (w / 2, h / 2), label, size, 600, WHITE if dark else INK, anchor='mm')
    im = finish_card(im)
    place_card(canvas, im, cx, cy, t, t0, 0)

def arrow(canvas, p0, p1, t, t0, dur=0.45, color=INK, width=4, dashed=False):
    q = smooth((t - t0) / dur)
    if q <= 0: return
    d = ImageDraw.Draw(canvas)
    (x0, y0), (x1, y1) = p0, p1
    xe, ye = lerp(x0, x1, q), lerp(y0, y1, q)
    if dashed:
        L = math.hypot(xe - x0, ye - y0); n = int(L // 18)
        for k in range(n):
            a = k * 18 / max(L, 1); b = min(1, (k * 18 + 10) / max(L, 1))
            d.line((lerp(x0, xe, a), lerp(y0, ye, a), lerp(x0, xe, b), lerp(y0, ye, b)), fill=color + (255,), width=width)
    else:
        d.line((x0, y0, xe, ye), fill=color + (255,), width=width)
    if q > 0.9:
        ang = math.atan2(y1 - y0, x1 - x0); s = 14
        pts = [(xe, ye), (xe - s * math.cos(ang - 0.45), ye - s * math.sin(ang - 0.45)), (xe - s * math.cos(ang + 0.45), ye - s * math.sin(ang + 0.45))]
        d.polygon(pts, fill=color + (255,))

def pointer(canvas, x, y, t, color=ORANGE):
    d = ImageDraw.Draw(canvas)
    dx = 6 * math.sin(t * 5)
    d.polygon([(x + dx, y - 12), (x + dx, y + 12), (x + dx + 18, y)], fill=color + (255,))

def bars_chart(canvas, t, t0, x0, y0, w, h, vals, hl=None, labels=None, step=0.06):
    d = ImageDraw.Draw(canvas)
    n = len(vals); bw = w / n * 0.62
    pa = smooth((t - t0) / 0.3)
    if pa <= 0: return
    d.line((x0, y0 + h, x0 + w, y0 + h), fill=(205, 201, 195, int(255 * pa)), width=2)
    for k, v in enumerate(vals):
        q = smooth((t - t0 - k * step) / 0.35)
        if q <= 0: continue
        x = x0 + k * w / n + (w / n - bw) / 2
        bh = h * v * q
        col = ORANGE if hl is not None and k == hl else (INK if hl is None or k > (hl or 0) else (214, 210, 204))
        if hl is None: col = INK if k == n - 1 else (214, 210, 204)
        d.rounded_rectangle((x, y0 + h - bh, x + bw, y0 + h), 5, fill=col + (255,))
        if labels:
            li, lb = text_img(labels[k], 18, 500, GREY)
            canvas.alpha_composite(li, (int(x + bw / 2 - li.width / 2), int(y0 + h + 10)))

def check_circle(canvas, x, y, r, t, t0):
    q = smooth((t - t0) / 0.35)
    if q <= 0: return
    d = ImageDraw.Draw(canvas)
    rr = r * (0.6 + 0.4 * ease_back(q))
    d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=GREEN + (int(255 * q),))
    m = smooth((t - t0 - 0.15) / 0.3)
    if m > 0:
        pts = [(x - rr * 0.42, y + rr * 0.02), (x - rr * 0.1, y + rr * 0.36), (x + rr * 0.45, y - rr * 0.32)]
        if m < 1:
            pts = pts[:2] + [(lerp(pts[1][0], pts[2][0], m), lerp(pts[1][1], pts[2][1], m))]
        d.line(pts, fill=WHITE + (255,), width=max(3, int(rr * 0.2)), joint='curve')


"""Estilo "papel quadriculado" (referência marianit2016, 09/11/2026) sobre a motion_lib.
- Fundo de papel quadriculado com vinheta; cenas de cor chapada (Exuberant Orange) para ênfase.
- Texto pesado (Inter Black/Bold) com destaque em Blue Violet, entrando com motion blur horizontal.
- Recortes em retícula com borda de papel rasgado (objetos ou foto enviada para o vídeo específico; não reutilize fotos entre vídeos), com desfoque de profundidade.
- Círculo tracejado girando.
Uso no arquivo de cenas:  from motion_papel import *  ;  install()  (troca render_top e draw_line da motion_lib).
Cena: {'s': t, 'bg': 'papel'|'cor', 'lines': [...], 'draw': f}
Estilos de palavra: r (SemiBold), b (Black tinta), a (Black azul), w (Black branco, para fundo de cor), m (Medium cinza).
"""
import math, os, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageEnhance
import motion_lib as M
from motion_lib import TW, TH, clamp, smooth, lerp, ease, ease_back, font, text_img

PAPER = (247, 246, 242); GRIDC = (218, 216, 211); INKP = (24, 23, 24); BLUE = (102, 91, 192)
ORANGE = (235, 99, 60); WHITE = (255, 255, 255); MUTED = (120, 116, 112)
EMOJI = '/System/Library/Fonts/Apple Color Emoji.ttc'

_cache = {}
def bg_papel():
    if 'papel' in _cache: return _cache['papel']
    S = 2
    im = Image.new('RGB', (TW * S, TH * S), PAPER)
    d = ImageDraw.Draw(im)
    step = 54
    for x in range(0, TW + 1, step): d.line((x * S, 0, x * S, TH * S), fill=GRIDC, width=S)
    for y in range(0, TH + 1, step): d.line((0, y * S, TW * S, y * S), fill=GRIDC, width=S)
    im = im.resize((TW, TH), Image.LANCZOS)
    yy, xx = np.mgrid[0:TH, 0:TW]
    r = np.sqrt(((xx - TW / 2) / (TW * 0.62)) ** 2 + ((yy - TH * 0.46) / (TH * 0.66)) ** 2)
    v = np.clip((r - 0.55) / 0.6, 0, 1) ** 1.6 * 0.42
    a = np.asarray(im).astype(float) * (1 - v[..., None])
    out = Image.fromarray(a.clip(0, 255).astype('uint8')).convert('RGBA')
    _cache['papel'] = out
    return out

def bg_cor(color=ORANGE):
    k = ('cor', color)
    if k in _cache: return _cache[k]
    yy, xx = np.mgrid[0:TH, 0:TW]
    r = np.sqrt(((xx - TW / 2) / (TW * 0.7)) ** 2 + ((yy - TH / 2) / (TH * 0.7)) ** 2)
    v = np.clip((r - 0.5) / 0.7, 0, 1) * 0.28
    base = np.ones((TH, TW, 3)) * np.array(color)
    out = Image.fromarray((base * (1 - v[..., None])).clip(0, 255).astype('uint8')).convert('RGBA')
    _cache[k] = out
    return out

# ---------- words with horizontal motion blur ----------
_wc = {}
def word_img(word, style, size):
    k = (word, style, size)
    if k in _wc: return _wc[k]
    w = {'r': 600, 'b': 900, 'a': 900, 'w': 900, 'm': 500}[style]
    col = {'r': INKP, 'b': INKP, 'a': BLUE, 'w': WHITE, 'm': MUTED}[style]
    im, base = text_img(word, size, w, col, False)
    _wc[k] = (im, base)
    return _wc[k]

def motion_blur(im, dist):
    """Rastro horizontal: cópias deslocadas com alfa decrescente."""
    if dist < 2: return im
    n = 7
    out = Image.new('RGBA', (im.width + int(dist) + 4, im.height), (0, 0, 0, 0))
    for k in range(n):
        a = (k + 1) / n
        c = im.copy(); c.putalpha(c.getchannel('A').point(lambda v, a=a: int(v * a * a / 1.6)))
        out.alpha_composite(c, (int(dist * (1 - k / (n - 1))), 0))
    out.alpha_composite(im, (0, 0))
    return out

def draw_line(canvas, t, line, alpha_out=1.0):
    t0, y, words, size = line[:4]
    stagger = line[4] if len(line) > 4 else 0.1
    ts = line[5] if len(line) > 5 else [t0 + i * stagger for i in range(len(words))]
    if t < ts[0] - 0.01: return
    imgs = [word_img(w, s if s in 'rbawm' else 'b', size) for w, s in words]
    sp = size * 0.22
    rw = 0.0
    for i, (im, b) in enumerate(imgs):
        rw += (im.width + (sp if i else 0)) * smooth((t - ts[i]) / 0.22)
    x = TW / 2 - rw / 2
    for i, (im, base) in enumerate(imgs):
        p = (t - ts[i]) / 0.26
        if p <= 0: break
        a = ease(clamp(p))
        off = 140 * (1 - a)
        img = im
        if a < 1:
            img = motion_blur(im, off * 0.9)
            img.putalpha(img.getchannel('A').point(lambda v: int(v * min(1, a * 1.6))))
        canvas.alpha_composite(img, (int(x - off), int(y - base)))
        x += im.width + sp

# ---------- halftone torn-paper stickers ----------
def halftone(src_rgba, cell=9, contrast=1.35):
    S = 3
    src = src_rgba.resize((src_rgba.width * S, src_rgba.height * S), Image.LANCZOS)
    a = src.getchannel('A').point(lambda v: 255 if v > 110 else 0).filter(ImageFilter.MedianFilter(7))
    flat = Image.new('RGB', src.size, (255, 255, 255)); flat.paste(src.convert('RGB'), mask=src.getchannel('A'))
    g = ImageOps.autocontrast(ImageOps.grayscale(flat), cutoff=2)
    g = ImageEnhance.Contrast(g).enhance(contrast)
    G = np.asarray(g).astype(float) / 255.0
    H, Wd = G.shape
    out = Image.new('L', (Wd, H), 255); d = ImageDraw.Draw(out)
    ca = sa = math.sqrt(0.5); R = int(math.hypot(Wd, H))
    for i in range(-R // cell, R // cell + 1):
        for j in range(-R // cell, R // cell + 1):
            u, v = i * cell, j * cell
            x = Wd / 2 + u * ca - v * sa; y = H / 2 + u * sa + v * ca
            if 0 <= x < Wd and 0 <= y < H:
                r = cell * 0.62 * math.sqrt(max(0, 1 - G[int(y), int(x)]))
                if r > 0.5: d.ellipse((x - r, y - r, x + r, y + r), fill=0)
    solid = g.point(lambda v: 0 if v < 38 else 255)
    out = Image.fromarray(np.minimum(np.asarray(out), np.asarray(solid)))
    ink = Image.new('RGBA', (Wd, H), (26, 24, 25, 255)); paper = Image.new('RGBA', (Wd, H), (246, 244, 240, 255))
    body = Image.composite(paper, ink, out); body.putalpha(a)
    rnd = np.random.default_rng(3)
    border = a.filter(ImageFilter.MaxFilter(41))
    noise = Image.fromarray((rnd.random((H // 10 + 1, Wd // 10 + 1)) * 255).astype('uint8')).resize((Wd, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(5))
    bn = np.asarray(border).astype(float) / 255 * 0.75 + np.asarray(noise).astype(float) / 255 * 0.5
    bm = Image.fromarray(((bn > 0.68) * 255).astype('uint8')).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.ModeFilter(5))
    bm = Image.fromarray(np.maximum(np.asarray(bm), np.asarray(a.filter(ImageFilter.MaxFilter(21)))))
    pad = 40
    st = Image.new('RGBA', (Wd + pad * 2, H + pad * 2), (0, 0, 0, 0))
    pap = Image.new('RGBA', (Wd, H), (250, 249, 246, 255)); pap.putalpha(bm)
    st.alpha_composite(pap, (pad, pad)); st.alpha_composite(body, (pad, pad))
    st = st.crop(st.getbbox())
    return st.resize((st.width * 2 // S, st.height * 2 // S), Image.LANCZOS)

def emoji_rgba(e):
    f = ImageFont.truetype(EMOJI, 160)
    im = Image.new('RGBA', (260, 260), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((30, 30), e, font=f, embedded_color=True)
    return im.crop(im.getbbox())

_st = {}
def sticker_img(key, cachedir=None):
    """key: caminho de PNG recortado (foto) ou um emoji. Gera e guarda o adesivo em retícula."""
    if key in _st: return _st[key]
    fn = None
    if cachedir:
        os.makedirs(cachedir, exist_ok=True)
        fn = os.path.join(cachedir, 'st_%s.png' % hashlib.md5(key.encode('utf-8')).hexdigest()[:12])
        if os.path.exists(fn):
            _st[key] = Image.open(fn).convert('RGBA'); return _st[key]
    if os.path.exists(key):
        im = Image.open(key).convert('RGBA')
        if not key.endswith('_pronto.png'):
            im = halftone(im)
    else:
        im = halftone(emoji_rgba(key).resize((320, 320), Image.LANCZOS), cell=8, contrast=1.15)
    if fn: im.save(fn)
    _st[key] = im
    return im

def place_sticker(canvas, im, cx, cy, h, t, t0, tilt=-4, dof=0.0, shadow=True):
    p = (t - t0) / 0.4
    if p <= 0: return
    sc = h / im.height * (0.7 + 0.3 * ease_back(clamp(p)))
    sc *= 1 + 0.012 * math.sin((t - t0) * 2.0)
    ang = tilt * (1 + 0.6 * (1 - ease(clamp(p)))) + 1.2 * math.sin((t - t0) * 1.3)
    im2 = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.BICUBIC).rotate(ang, resample=Image.BICUBIC, expand=True)
    if dof > 0: im2 = im2.filter(ImageFilter.GaussianBlur(dof))
    if p < 1: im2.putalpha(im2.getchannel('A').point(lambda v: int(v * smooth(p * 1.5))))
    y = cy + 6 * math.sin((t - t0) * 1.6)
    if shadow:
        pad = 40
        sh = Image.new('RGBA', (im2.width + pad * 2, im2.height + pad * 2), (0, 0, 0, 0))
        s1 = Image.new('RGBA', im2.size, (20, 18, 16, 0)); s1.putalpha(im2.getchannel('A').point(lambda v: int(v * 0.3)))
        sh.paste(s1, (pad + 8, pad + 20)); sh = sh.filter(ImageFilter.GaussianBlur(16 + dof))
        canvas.alpha_composite(sh, (int(cx - im2.width / 2 - pad), int(y - im2.height / 2 - pad)))
    canvas.alpha_composite(im2, (int(cx - im2.width / 2), int(y - im2.height / 2)))

def dashed_circle(canvas, cx, cy, r, t, t0, color=BLUE, width=10, dashes=14):
    p = ease(clamp((t - t0) / 0.5))
    if p <= 0: return
    S = 2
    im = Image.new('RGBA', (int(r * 2 + width * 2) * S, int(r * 2 + width * 2) * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im); o = width * S
    rot = (t - t0) * 40
    seg = 360 / dashes
    for k in range(int(dashes * p) + 1):
        a0 = rot + k * seg
        d.arc((o, o, o + 2 * r * S, o + 2 * r * S), a0, a0 + seg * 0.55, fill=color + (255,), width=width * S)
    im = im.resize((im.width // S, im.height // S), Image.LANCZOS)
    canvas.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

def swirl(canvas, t, t0, pts, color=WHITE, width=5, dur=0.9):
    """Linha orgânica que se desenha (como o fio da cena do coração na referência)."""
    q = ease(clamp((t - t0) / dur))
    if q <= 0: return
    n = len(pts); m = max(2, int((n - 1) * q) + 1)
    S = 2
    im = Image.new('RGBA', (TW * S, TH * S), (0, 0, 0, 0))
    ImageDraw.Draw(im).line([(x * S, y * S) for x, y in pts[:m]], fill=color + (255,), width=width * S, joint='curve')
    canvas.alpha_composite(im.resize((TW, TH), Image.LANCZOS))

def wave_pts(x0, y0, x1, y1, amp=60, waves=1.5, n=80):
    out = []
    for k in range(n):
        u = k / (n - 1)
        x = lerp(x0, x1, u) + amp * math.sin(u * math.pi * 2 * waves)
        y = lerp(y0, y1, u)
        out.append((x, y))
    return out

# ---------- render_top with per-scene background ----------
def render_top(SC, t):
    idx = max(i for i, s in enumerate(SC) if s['s'] <= t)
    sc = SC[idx]
    frame = (bg_cor(sc.get('color', ORANGE)) if sc.get('bg') == 'cor' else bg_papel()).copy()
    canvas = Image.new('RGBA', (TW, TH), (0, 0, 0, 0))
    out = 1 - smooth((t - (sc['e'] - 0.16)) / 0.16) if sc['e'] < M.DUR else 1
    if 'draw' in sc: sc['draw'](canvas, t)
    for ln in sc['lines']:
        draw_line(canvas, t, ln)
    if out < 1:
        canvas = canvas.filter(ImageFilter.GaussianBlur(8 * (1 - out)))
        canvas.putalpha(canvas.getchannel('A').point(lambda v: int(v * out)))
    life = clamp((t - sc['s']) / max(1.0, sc['e'] - sc['s']))
    z = 1.0 + 0.05 * life
    cw, ch = int(TW * z), int(TH * z)
    canvas = canvas.resize((cw, ch), Image.BICUBIC).rotate(0.6 * math.sin(life * math.pi), resample=Image.BICUBIC)
    canvas = canvas.crop(((cw - TW) // 2, (ch - TH) // 2, (cw - TW) // 2 + TW, (ch - TH) // 2 + TH))
    frame.alpha_composite(canvas)
    # entrada da cena: flash de deslocamento
    if idx > 0 and t - sc['s'] < 0.12:
        q = (t - sc['s']) / 0.12
        frame = frame.filter(ImageFilter.GaussianBlur(4 * (1 - q)))
    return frame

_PSC = []
_orig_caption = M.caption_layer
def caption_layer(t, lay):
    """Em cena de cor chapada a legenda fica branca e o grifo vira tarja escura."""
    cor = False
    if _PSC:
        idx = max(i for i, s in enumerate(_PSC) if s['s'] <= t)
        cor = _PSC[idx].get('bg') == 'cor'
    if not cor:
        return _orig_caption(t, lay)
    ink, hl = M.INK, M.HL
    M.INK, M.HL = WHITE, INKP
    try:
        _orig_caption(t, lay)
    finally:
        M.INK, M.HL = ink, hl

def install(SC=None):
    M.render_top = render_top
    M.draw_line = draw_line
    M.caption_layer = caption_layer
    if SC is not None:
        _PSC[:] = SC

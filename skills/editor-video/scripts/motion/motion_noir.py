"""Linguagem "Noir editorial + vidro líquido" (exemplo).
Pôster suíço escuro, fotografia P&B, granulação, aberração cromática e refração real de vidro.
Tudo em numpy/cv2: as imagens trafegam como float32 RGB 0..1 (H, W, 3).
"""
import os, sys, math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

SK = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, os.path.join(SK, 'scripts', 'motion'))
FONTS = os.path.join(SK, 'assets', 'fonts')
INTER = os.path.join(FONTS, 'Inter.ttf'); INTERI = os.path.join(FONTS, 'InterItalic.ttf')
SERIF = os.path.join(FONTS, 'InstrumentSerif-Italic.ttf')

INK = np.array([0.075, 0.07, 0.072], np.float32)       # Darkest Hour, quase preto
PAPER = np.array([0.94, 0.933, 0.918], np.float32)     # Cloud Dancer
ACCENT = np.array([0.92, 0.39, 0.235], np.float32)     # Exuberant Orange (o "vermelho" da paleta)
SUN = np.array([0.88, 0.996, 0.32], np.float32)

W_, H_ = 1080, 1920

# ------------------------------------------------------------ tipografia
_fc = {}
def F(path, size, wght=None):
    k = (path, size, wght)
    if k not in _fc:
        f = ImageFont.truetype(path, size)
        if wght:
            try: f.set_variation_by_axes([32, wght])
            except Exception: pass
        _fc[k] = f
    return _fc[k]

def text_mask(s, font, track=0.0):
    """Máscara L (0..255) do texto, recortada no bbox de tinta. Retorna (mask, ascender_offset)."""
    asc, desc = font.getmetrics()
    w = int(font.getlength(s) + abs(track) * len(s) * font.size + font.size)
    im = Image.new('L', (w, asc + desc + font.size // 2), 0)
    d = ImageDraw.Draw(im)
    if track:
        x = font.size * 0.1
        for ch in s:
            d.text((x, font.size * 0.1), ch, font=font, fill=255)
            x += font.getlength(ch) + track * font.size
    else:
        d.text((font.size * 0.1, font.size * 0.1), s, font=font, fill=255)
    bb = im.getbbox() or (0, 0, 1, 1)
    return im.crop(bb)

def stamp(img, mask, x, y, color, alpha=1.0):
    """Pinta `color` em img (float) através da máscara L, com (x,y) = canto superior esquerdo."""
    m = np.asarray(mask, np.float32) / 255.0 * alpha
    h, w = m.shape
    x0, y0 = int(round(x)), int(round(y))
    xa, ya = max(0, x0), max(0, y0); xb, yb = min(img.shape[1], x0 + w), min(img.shape[0], y0 + h)
    if xa >= xb or ya >= yb: return
    mm = m[ya - y0:yb - y0, xa - x0:xb - x0, None]
    img[ya:yb, xa:xb] = img[ya:yb, xa:xb] * (1 - mm) + np.asarray(color, np.float32) * mm

# ------------------------------------------------------------ acabamento de filme
def grain(img, seed, amount=0.055):
    rng = np.random.default_rng(seed)
    n = rng.standard_normal(img.shape[:2]).astype(np.float32)
    n = cv2.GaussianBlur(n, (0, 0), 0.7)
    lum = img.mean(2, keepdims=True)
    w = amount * (0.55 + 0.9 * lum * (1 - lum) * 4) * 0.6 + amount * 0.4
    return np.clip(img + n[..., None] * w, 0, 1)

def chroma(img, px=2.0):
    """Aberração cromática radial: R para fora, B para dentro, mais forte nas bordas."""
    if px <= 0.05: return img
    h, w = img.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = w / 2, h / 2
    dx, dy = (xx - cx) / w, (yy - cy) / h
    r = np.sqrt(dx * dx + dy * dy) * 2
    out = img.copy()
    for ch, k in ((0, 1.0), (2, -1.0)):
        mx = xx + dx * r * px * k * 2; my = yy + dy * r * px * k * 2
        out[..., ch] = cv2.remap(img[..., ch], mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return out

_vig = {}
def vignette(img, strength=0.45):
    h, w = img.shape[:2]
    k = (h, w, strength)
    if k not in _vig:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        r = np.sqrt(((xx - w / 2) / (w * 0.62)) ** 2 + ((yy - h * 0.48) / (h * 0.62)) ** 2)
        _vig[k] = (1 - strength * np.clip((r - 0.45) / 0.75, 0, 1) ** 1.5)[..., None]
    return img * _vig[k]

def finish(img, t, chroma_px=1.6, grain_amt=0.05, vig=0.42):
    img = vignette(img, vig)
    img = chroma(img, chroma_px)
    return grain(img, int(t * 30) + 7, grain_amt)

# ------------------------------------------------------------ fotografia P&B
def bw_photo(rgba, contrast=1.35, gamma=0.95, lift=0.03):
    """RGBA uint8 -> (rgb float P&B com contraste de filme, alpha float)."""
    a = np.asarray(rgba, np.float32) / 255.0
    rgb, al = a[..., :3], a[..., 3]
    l = rgb @ np.array([0.30, 0.59, 0.11], np.float32)
    l = np.clip((l - 0.5) * contrast + 0.5, 0, 1) ** gamma
    l = lift + l * (1 - lift)
    return np.repeat(l[..., None], 3, 2), al

def paste(img, rgb, al, x, y, opacity=1.0):
    h, w = al.shape
    x0, y0 = int(x), int(y)
    xa, ya = max(0, x0), max(0, y0); xb, yb = min(img.shape[1], x0 + w), min(img.shape[0], y0 + h)
    if xa >= xb or ya >= yb: return
    m = al[ya - y0:yb - y0, xa - x0:xb - x0, None] * opacity
    img[ya:yb, xa:xb] = img[ya:yb, xa:xb] * (1 - m) + rgb[ya - y0:yb - y0, xa - x0:xb - x0] * m

# ------------------------------------------------------------ vidro líquido (refração)
def glyph_height(s, font_path, size, wght=900, soft=0.05, pad=None):
    """Mapa de altura (float 0..1) de um glifo inflado (perfil acolchoado, borda nítida)."""
    f = F(font_path, size, wght)
    m = text_mask(s, f)
    pad = pad or int(size * 0.2)
    m2 = Image.new('L', (m.width + 2 * pad, m.height + 2 * pad), 0); m2.paste(m, (pad, pad))
    a = np.asarray(m2, np.float32) / 255.0
    b = cv2.GaussianBlur(a, (0, 0), size * soft)
    h = np.clip((b - 0.32) / 0.68, 0, 1)
    h = np.sqrt(h) * (b > 0.32)
    return cv2.GaussianBlur(h.astype(np.float32), (0, 0), 1.2)

def blob_height(shape, balls, t):
    """Metaballs: balls = [(cx, cy, r, fase)] em px. Retorna altura 0..1 (forma orgânica de gota)."""
    h, w = shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    f = np.zeros((h, w), np.float32)
    for cx, cy, r, ph in balls:
        cx2 = cx + r * 0.35 * math.sin(t * 1.3 + ph); cy2 = cy + r * 0.3 * math.cos(t * 1.1 + ph * 1.7)
        f += r * r / ((xx - cx2) ** 2 + (yy - cy2) ** 2 + 1)
    hgt = np.clip((f - 1.0) / 1.6, 0, 1)
    return cv2.GaussianBlur(np.sqrt(hgt), (0, 0), 3)

def refract(bg, hgt, x, y, strength=60.0, dispersion=0.25, rot=0.0, refl=0.75, edge=0.8, env_phase=0.0):
    """Lente de vidro com mapa de altura `hgt` em (x, y) sobre bg (float RGB).
    Refração com dispersão (canais separados) + reflexo de estúdio (faixas de luz) pesado pela
    Fresnel + contorno escuro. Linguagem das referências Speeld (gota) e Panter (letra de vidro)."""
    hgt = np.asarray(hgt, np.float32)
    if abs(rot) > 0.01:
        hh, ww = hgt.shape
        M = cv2.getRotationMatrix2D((ww / 2, hh / 2), rot, 1.0)
        hgt = cv2.warpAffine(hgt, M, (ww, hh))
    h, w = hgt.shape
    x0, y0 = int(x), int(y)
    xa, ya = max(0, x0), max(0, y0); xb, yb = min(bg.shape[1], x0 + w), min(bg.shape[0], y0 + h)
    if xb - xa < 4 or yb - ya < 4: return bg
    H = hgt[ya - y0:yb - y0, xa - x0:xb - x0]
    gy, gx = np.gradient(H)
    K = 22.0
    nzr = 1.0 / np.sqrt(1 + (gx * K) ** 2 + (gy * K) ** 2)
    nx, ny = -gx * K * nzr, -gy * K * nzr
    mask = np.clip(H * 40, 0, 1)
    out = bg.copy()
    yy, xx = np.mgrid[ya:yb, xa:xb].astype(np.float32)
    for c, k in enumerate((1 - dispersion, 1.0, 1 + dispersion)):
        mx = (xx + nx * strength * k).astype(np.float32)
        my = (yy + ny * strength * k).astype(np.float32)
        samp = cv2.remap(bg[..., c], mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        out[ya:yb, xa:xb, c] = bg[ya:yb, xa:xb, c] * (1 - mask) + samp * mask
    # reflexo de estúdio: faixas de luz indexadas pela normal
    u = ny * 2.6 + nx * 0.9 + env_phase
    env = np.clip(np.sin(u * 3.1) * 2.2 - 0.6, 0, 1) ** 1.5
    env += np.clip(np.sin(u * 7.3 + 1.1) * 3 - 2.2, 0, 1) * 0.6
    fres = np.clip((1 - nzr) * 1.6, 0, 1) ** 1.4
    rim = np.clip((1 - nzr) * 3.0, 0, 1) ** 3 * edge          # contorno escuro grosso
    L = np.array([-0.5, -0.65, 0.57]); L = L / np.linalg.norm(L)
    d = np.clip(nx * L[0] + ny * L[1] + nzr * L[2], 0, 1)
    spec = d ** 60 * 1.2
    reg = out[ya:yb, xa:xb]
    m3 = mask[..., None]
    reg = reg * (1 - (fres * refl)[..., None] * m3) + (env * fres * refl)[..., None] * m3
    reg = reg * (1 - (rim * 0.9)[..., None] * m3)
    reg = reg + (spec)[..., None] * m3
    out[ya:yb, xa:xb] = np.clip(reg, 0, 1)
    return out

# ------------------------------------------------------------ grade de pôster (metadados)
def poster_meta(img, t, color=PAPER, alpha=0.62, section='SEÇÃO', idx='01 / 06', code='EX-01'):
    f = F(INTER, 22, 500); fb = F(INTER, 22, 700)
    c = color
    def ln(y, x0=48, x1=W_ - 48, a=0.35):
        img[y:y + 2, x0:x1] = img[y:y + 2, x0:x1] * (1 - a) + np.asarray(c) * a
    stamp(img, text_mask('SUA MARCA', fb), 48, 52, c, alpha)
    stamp(img, text_mask('Editorial · IA aplicada', f), 48, 80, c, alpha * 0.7)
    s = text_mask(code + ' — ' + idx, f); stamp(img, s, W_ - 48 - s.width, 52, c, alpha)
    tc = '%02d:%05.2f' % (int(t // 60), t % 60)
    s = text_mask('TC ' + tc, f); stamp(img, s, W_ - 48 - s.width, 80, c, alpha * 0.7)
    ln(118)
    s = text_mask(section, fb, track=0.12); stamp(img, s, 48, 136, c, alpha * 0.85)
    for k in range(6):  # ////// marcador
        x = W_ - 48 - 14 * (6 - k)
        cv2.line(img, (x, 156), (x + 9, 138), tuple(float(v) for v in c * alpha), 2, cv2.LINE_AA)

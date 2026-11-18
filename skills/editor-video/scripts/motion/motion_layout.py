"""Camada v0.5 do motion: mascote em pixel art, headline de abertura na divisória,
cartão de vidro e quadros por MODO DE LAYOUT (tela dividida, rosto em tela cheia, apresentador em cartão).

Uso no arquivo de cenas (depois de importar motion_lib / motion_papel e definir SC):
    from motion_layout import *
    LAYOUT = [(0.0, 'split'), (36.4, 'rosto'), (38.6, 'split'), (53.7, 'cartao'), ...]  # (início, modo)
    HEADLINE = ('3 formas de automatizar', 'com Claude')                                    # 2 linhas curtas
    configure(SC, LAYOUT, HEADLINE)
render_motion.py chama M.render_frame(t) se existir; compor.py lê W/layout.json para montar o vídeo.

Modos (tela 1080x1920):
- split : painel de motion 1080x960 em cima, vídeo 1080x960 embaixo (padrão).
- rosto : vídeo do apresentador em tela cheia; sobre ele só a legenda grande (terço inferior) e, se houver, o mascote.
- cartao: fundo do motion em tela cheia; as cenas ocupam a metade de cima e o apresentador aparece num
          cartão de cantos arredondados (CARD_BOX) na metade de baixo, com sombra.
"""
import json, math, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import motion_lib as M
from motion_lib import TW, TH, clamp, smooth, lerp, ease, ease_back, text_img, font

HERE = os.path.dirname(os.path.abspath(__file__))
SERIF_I = os.path.join(HERE, '..', '..', 'assets', 'fonts', 'InstrumentSerif-Italic.ttf')

INK = (32, 30, 31); CREAM = (243, 240, 236); ORANGE = (235, 99, 60); BLUE = (102, 91, 192); HL = (225, 254, 82)
W_, H_ = 1080, 1920
CARD_BOX = (130, 1010, 950, 1830)     # x0, y0, x1, y1 do cartão do apresentador no modo 'cartao'
CARD_RADIUS = 44
MIN_ON_SCREEN = 1.2                    # segundos mínimos de um elemento na tela (checado por checar_tempos)

# ------------------------------------------------------------------ mascote
# Personagem genérico: corpo arredondado com um olho grande.
# 16x16, cada caractere é um pixel. b=corpo, d=sombra do corpo, w=branco do olho, k=pupila, y=brilho, o=boca, .=vazio
_BASE = [
    "................",
    ".....bbbbbb.....",
    "...bbbbbbbbbb...",
    "..bbbbbbbbbbbb..",
    "..bbbwwwwwwbbb..",
    ".bbbwwwwwwwwbbb.",
    ".bbbwwwkkwwwbbb.",
    ".bbbwwkkkywwbbb.",
    ".bbbwwwkkwwwbbb.",
    ".bbbbwwwwwwbbbb.",
    ".bbbbbbbbbbbbbb.",
    ".bbbbbboobbbbbb.",
    "..bbbbbbbbbbbb..",
    "..dbbbbbbbbbbd..",
    "...dd..dd..dd...",
    "................",
]
_PAL = {'b': BLUE, 'd': (74, 64, 150), 'w': (255, 255, 255), 'k': INK, 'y': HL, 'o': INK}

def _grid(pose, blink=False):
    g = [list(r) for r in _BASE]
    if blink:
        for x in range(4, 12):
            for y in (4, 5, 6, 7, 8, 9):
                if g[y][x] in 'wky': g[y][x] = 'b'
        for x in range(5, 11): g[7][x] = 'k'
    if pose == 'acena':            # braço direito para cima
        for y, x in ((4, 15), (5, 15), (6, 14), (7, 14)): g[y][x] = 'b'
    elif pose == 'aponta':         # braço esquerdo apontando para o lado
        for x in (0,): g[9][x] = 'b'
        g[9][0] = 'b'; g[8][0] = 'b'
    elif pose == 'pensa':          # olho olhando para cima + pupila deslocada
        for y in (6, 7, 8):
            for x in range(4, 12):
                if g[y][x] in 'ky': g[y][x] = 'w'
        g[5][7] = 'k'; g[5][8] = 'k'; g[6][7] = 'k'; g[6][8] = 'y'
    elif pose == 'comemora':       # dois braços para cima + boca aberta
        for y, x in ((3, 0), (4, 0), (5, 1), (3, 15), (4, 15), (5, 14)): g[y][x] = 'b'
        g[11][7] = 'o'; g[11][8] = 'o'; g[12][7] = 'o'; g[12][8] = 'o'
    return g

_mc = {}
def mascot_img(pose='neutro', size=220, blink=False):
    k = (pose, size, blink)
    if k in _mc: return _mc[k]
    g = _grid(pose, blink)
    im = Image.new('RGBA', (16, 16), (0, 0, 0, 0)); px = im.load()
    for y, row in enumerate(g):
        for x, c in enumerate(row):
            if c in _PAL: px[x, y] = _PAL[c] + (255,)
    im = im.resize((size, size), Image.NEAREST)
    _mc[k] = im
    return im

def draw_mascot(canvas, t, t0, cx, cy, size=200, pose='neutro', bob=True):
    """Entra com pulo (squash and stretch), pisca a cada ~2,6 s e flutua."""
    p = (t - t0) / 0.45
    if p <= 0: return
    blink = ((t - t0) % 2.6) < 0.12
    im = mascot_img(pose, size, blink)
    e = ease_back(clamp(p))
    sy = 1 + 0.12 * math.sin(clamp(p) * math.pi) ; sx = 2 - sy
    hop = (1 - e) * 120
    y = cy - hop + (6 * math.sin((t - t0) * 3.0) if bob else 0)
    w, h = int(im.width * sx), int(im.height * sy)
    im2 = im.resize((max(1, w), max(1, h)), Image.NEAREST)
    if p < 1: im2.putalpha(im2.getchannel('A').point(lambda v: int(v * smooth(p * 1.6))))
    sh = Image.new('RGBA', (w, max(8, h // 8)), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse((0, 0, w - 1, sh.height - 1), fill=(0, 0, 0, int(55 * smooth(p))))
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)), (int(cx - w / 2), int(cy + h / 2 - sh.height / 2)))
    canvas.alpha_composite(im2, (int(cx - w / 2), int(y - h / 2)))

# ------------------------------------------------------------------ headline de abertura
def serif(size):
    return ImageFont.truetype(SERIF_I, size)

def headline_layer(t, lines, y_center=960, dur=4.0, color=ORANGE):
    """Faixa sólida atravessando a divisória, texto branco em serifada itálica centralizado.
    Já aparece completa no quadro 0 (capa) e sai entre dur-0,35 s e dur."""
    if t >= dur: return None
    out = 1 - smooth((t - (dur - 0.35)) / 0.35)
    f = serif(84)
    lh = 86
    band_h = 40 + lh * len(lines)
    lay = Image.new('RGBA', (W_, H_), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    grow = 1.0 if t <= 0 else min(1.0, 0.94 + 0.06 * ease(t / 0.6))
    bw = int(W_ * grow)
    y0 = int(y_center - band_h / 2)
    d.rectangle(((W_ - bw) // 2, y0, (W_ + bw) // 2, y0 + band_h), fill=color + (255,))
    for i, s in enumerate(lines):
        d.text((W_ / 2, y0 + 20 + lh * i + lh / 2), s, font=f, fill=(255, 255, 255, 255), anchor='mm')
    if out < 1:
        lay.putalpha(lay.getchannel('A').point(lambda v: int(v * out)))
    return lay

# ------------------------------------------------------------------ cartão de vidro
def glass_card(canvas, box, t, t0, radius=28, tint=0.38, blur=22):
    """Vidro: desfoca o que já está no canvas atrás do retângulo, véu branco translúcido, borda clara
    e brilho no topo. Use em UM elemento por cena (o principal). Retorna a caixa para desenhar o conteúdo."""
    p = clamp((t - t0) / 0.4)
    if p <= 0: return None
    x0, y0, x1, y1 = [int(v) for v in box]
    region = canvas.crop((x0, y0, x1, y1))
    bg = region.filter(ImageFilter.GaussianBlur(blur))
    veil = Image.new('RGBA', region.size, (255, 255, 255, int(255 * tint)))
    bg.alpha_composite(veil)
    hi = Image.new('RGBA', region.size, (0, 0, 0, 0)); dh = ImageDraw.Draw(hi)
    for k in range(int(region.height * 0.35)):
        a = int(70 * (1 - k / (region.height * 0.35)))
        dh.line((0, k, region.width, k), fill=(255, 255, 255, a))
    bg.alpha_composite(hi)
    mask = Image.new('L', region.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, region.width - 1, region.height - 1), radius, fill=int(255 * smooth(p)))
    sh = Image.new('RGBA', (region.width + 80, region.height + 80), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((40, 52, 40 + region.width, 52 + region.height), radius, fill=(20, 18, 16, int(40 * smooth(p))))
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)), (x0 - 40, y0 - 40))
    canvas.paste(bg, (x0, y0), mask)
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle((x0, y0, x1, y1), radius, outline=(255, 255, 255, int(200 * smooth(p))), width=2)
    return (x0, y0, x1, y1)

# ------------------------------------------------------------------ legenda do modo rosto
def caption_rosto(t, lay, y=1560, size=58):
    """Legenda grande sobre o rosto: Inter Bold branca com sombra; palavra-chave com tarja Sun Glare e texto escuro."""
    for c in M.CH:
        if not (c['s'] - 0.02 <= t < c['e']): continue
        imgs = []
        for j, w in enumerate(c['words']):
            key = j in c['keys']
            imgs.append((text_img(w, size, 800, INK if key else (255, 255, 255)), key))
        sp = size * 0.26
        total = sum(im.width for (im, b), k in imgs) + sp * (len(imgs) - 1)
        x = W_ / 2 - total / 2
        for j, ((im, base), key) in enumerate(imgs):
            p = smooth((t - c['ws'][j] + 0.04) / 0.14)
            if p > 0:
                if key:
                    hl = Image.new('RGBA', (im.width + 20, int(size * 0.92)), HL + (int(255 * p),))
                    lay.alpha_composite(hl, (int(x - 10), int(y - size * 0.76)))
                else:
                    sh = im.getchannel('A').filter(ImageFilter.GaussianBlur(8)).point(lambda v: int(v * 0.75 * p))
                    s1 = Image.new('RGBA', im.size, (0, 0, 0, 0)); s1.putalpha(sh)
                    lay.alpha_composite(s1, (int(x), int(y - base + 4)))
                img = im if p >= 1 else im.copy()
                if p < 1: img.putalpha(im.getchannel('A').point(lambda v: int(v * p)))
                lay.alpha_composite(img, (int(x), int(y - base)))
            x += im.width + sp
        break

# ------------------------------------------------------------------ quadros por modo
CFG = {'SC': None, 'LAYOUT': [(0.0, 'split')], 'HEADLINE': None, 'MASCOTE': [], 'BG_FULL': None}

def configure(SC, layout, headline=None, mascote=None, bg_full=None):
    """layout: [(início, modo)], modos 'split' | 'rosto' | 'cartao'. mascote: [(t0, t1, pose, x, y, size, modo|None)].
    bg_full: função () -> Image RGBA 1080x1920 para o fundo do modo 'cartao' (padrão: estende o fundo do painel)."""
    CFG.update(SC=SC, LAYOUT=sorted(layout), HEADLINE=headline, MASCOTE=mascote or [], BG_FULL=bg_full)
    M.render_frame = render_frame

def mode_at(t):
    m = CFG['LAYOUT'][0][1]
    for s, mm in CFG['LAYOUT']:
        if s <= t: m = mm
    return m

def export_layout(path):
    """Grava os intervalos de modo para o compor.py."""
    L = CFG['LAYOUT']; out = []
    for i, (s, m) in enumerate(L):
        e = L[i + 1][0] if i + 1 < len(L) else M.DUR + 1
        out.append({'s': s, 'e': e, 'modo': m})
    json.dump(out, open(path, 'w'), ensure_ascii=False)

def _bg_full():
    if CFG['BG_FULL']: return CFG['BG_FULL']()
    top = M.render_top([{'s': 0, 'e': 1e9, 'lines': []}], 0)  # fundo vazio do estilo ativo
    full = Image.new('RGBA', (W_, H_))
    full.paste(top, (0, 0)); full.paste(top.transpose(Image.FLIP_TOP_BOTTOM), (0, TH))
    return full

_bgc = {}
def render_frame(t):
    modo = mode_at(t)
    out = Image.new('RGBA', (W_, H_), (0, 0, 0, 0))
    if modo == 'split':
        top = M.render_top(CFG['SC'], t)
        M.caption_layer(t, top)
        out.paste(top, (0, 0))
    elif modo == 'cartao':
        if 'full' not in _bgc: _bgc['full'] = _bg_full()
        out = _bgc['full'].copy()
        top = M.render_top(CFG['SC'], t)
        M.caption_layer(t, top)
        out.paste(top.crop((0, 0, TW, TH)), (0, 0))
        x0, y0, x1, y1 = CARD_BOX
        sh = Image.new('RGBA', (x1 - x0 + 120, y1 - y0 + 120), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((60, 78, 60 + x1 - x0, 78 + y1 - y0), CARD_RADIUS, fill=(20, 18, 16, 70))
        out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(26)), (x0 - 60, y0 - 60))
        hole = Image.new('L', (W_, H_), 255)
        ImageDraw.Draw(hole).rounded_rectangle(CARD_BOX, CARD_RADIUS, fill=0)
        a = out.getchannel('A'); a = Image.fromarray(__import__('numpy').minimum(__import__('numpy').asarray(a), __import__('numpy').asarray(hole)))
        out.putalpha(a)
        ImageDraw.Draw(out).rounded_rectangle(CARD_BOX, CARD_RADIUS, outline=(255, 255, 255, 230), width=4)
    elif modo == 'rosto':
        caption_rosto(t, out)
    for (t0, t1, pose, x, y, size, only) in CFG['MASCOTE']:
        if t0 - 0.01 <= t < t1 and (only is None or only == modo):
            draw_mascot(out, t, t0, x, y, size, pose)
    hl = CFG['HEADLINE']
    if hl:
        lay = headline_layer(t, hl)
        if lay is not None: out.alpha_composite(lay)
    return out

def checar_tempos(SC, eventos, minimo=MIN_ON_SCREEN):
    """eventos: [(tempo_de_entrada, descrição)]. Avisa elementos que ficam menos de `minimo` s antes da troca de cena."""
    avisos = []
    for t, desc in eventos:
        fim = next((s['e'] for s in SC if s['s'] <= t < s['e']), None)
        if fim is not None and fim - t < minimo:
            avisos.append(f'{desc} entra em {t:.2f}s e fica {fim - t:.2f}s')
    return avisos

# ------------------------------------------------------------------ abertura com frase-gancho (exemplo em 10/11/2026)
SUN = (225, 254, 82)
_HW = {}
def _hword(w, size, col):
    k = (w, size, col)
    if k not in _HW: _HW[k] = text_img(w, size, 900, col, False)
    return _HW[k]

def hook_frase(c, t, rows, numero_t=(0.2, 0.3), grifo=None, barra=(4.0, BLUE), mascote=None):
    """Frase-gancho em CAIXA ALTA, Inter Black, palavra por palavra no tempo da fala (exemplo).
    rows: [(y, tamanho, [(PALAVRA, t0, cor), ...]), ...]; até 5 linhas no painel de 1080x840 úteis.
    - Cada palavra bate: entra 1,9x maior e assenta em 0,2 s.
    - Se a primeira palavra for um número, ela começa gigante no centro (quadro 0 = capa) e voa para o lugar
      entre numero_t[0] e numero_t[0] + numero_t[1]. Use t0 = -0.2 nessa palavra.
    - grifo: (PALAVRA, t0) recebe a tarja Sun Glare varrendo da esquerda.
    - barra: (duração, cor) barra de progresso em y=790; None desliga.
    - mascote: (t0, x, y, tamanho, pose) ou None."""
    d = ImageDraw.Draw(c)
    first = True
    for y, size, words in rows:
        imgs = [_hword(w, size, col) for w, t0, col in words]
        sp = size * 0.24
        total = sum(im.width for im, b in imgs) + sp * (len(imgs) - 1)
        x = 540 - total / 2
        for (w, t0, col), (im, base) in zip(words, imgs):
            p = (t - t0 + 0.1) / 0.2
            num = first and w.isdigit(); first = False
            if p > 0:
                e = ease(clamp(p)); sc = 1 + 0.9 * (1 - e)
                if grifo and w == grifo[0]:
                    q = smooth((t - grifo[1]) / 0.22)
                    if q > 0:
                        d.rectangle((x - 18, y - size * 0.6, x - 18 + (im.width + 36) * q, y + size * 0.32), fill=SUN + (255,))
                cx = x + im.width / 2
                if num:
                    g = ease(clamp((t - numero_t[0]) / numero_t[1]))
                    big = 5.2 * (1 - g) + g
                    img = im.resize((max(1, int(im.width * big)), max(1, int(im.height * big))), Image.BICUBIC)
                    cxx = 540 * (1 - g) + cx * g
                    cyy = 440 * (1 - g) + (y - base + im.height / 2) * g
                    s0 = numero_t[0]
                    if s0 < t < s0 + numero_t[1]:
                        from motion_papel import motion_blur
                        img = motion_blur(img, 50 * math.sin(math.pi * (t - s0) / numero_t[1]))
                    c.alpha_composite(img, (int(cxx - img.width / 2), int(cyy - img.height / 2)))
                else:
                    img = im if sc <= 1.01 else im.resize((int(im.width * sc), int(im.height * sc)), Image.BICUBIC)
                    if p < 1:
                        img = img.copy(); img.putalpha(img.getchannel('A').point(lambda v, p=p: int(v * min(1, p * 2))))
                    c.alpha_composite(img, (int(cx - img.width / 2), int(y - base * sc + size * 0.36 * sc - size * 0.36)))
            x += im.width + sp
    if barra:
        q = clamp(t / barra[0])
        d.rectangle((90, 790, 90 + 900 * ease(q), 798), fill=barra[1] + (255,))
    if mascote and t >= mascote[0]:
        draw_mascot(c, t, mascote[0], mascote[1], mascote[2], mascote[3], mascote[4])

def camera_kicks(SC, kicks, tremores=(), ate=4.7):
    """Pancadas de câmera no painel de cima durante a abertura. kicks: [(t, intensidade)] (0,03 por palavra,
    0,06 a 0,09 nas palavras-chave); tremores: tempos com tremor de 0,3 s. Chame depois de install(SC)."""
    rt = M.render_top
    def wrapped(SCx, t):
        fr = rt(SCx, t)
        if SCx is not SC or t >= ate: return fr
        z = 1.0 + sum(a * math.exp(-(t - tk) * 9) for tk, a in kicks if t >= tk - 0.001)
        dx = dy = 0.0
        for th in tremores:
            u = t - th
            if 0 <= u < 0.3:
                dx += 16 * math.sin(u * 95) * (1 - u / 0.3); dy += 10 * math.cos(u * 80) * (1 - u / 0.3)
        if z <= 1.001 and not dx: return fr
        w, h = fr.size; cw, ch = int(w * z), int(h * z)
        big = fr.resize((cw, ch), Image.BICUBIC)
        x0 = max(0, min(cw - w, int((cw - w) / 2 + dx))); y0 = max(0, min(ch - h, int((ch - h) / 2 + dy)))
        return big.crop((x0, y0, x0 + w, y0 + h))
    M.render_top = wrapped

def headline_dur(dur):
    """Estende a faixa da divisória até o fim da abertura (ex.: 4,7 s)."""
    global headline_layer
    base = headline_layer
    headline_layer = lambda t, lines, **k: base(t, lines, dur=dur, **k)

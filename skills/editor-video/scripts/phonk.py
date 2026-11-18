"""Trilha original estilo drift phonk, sintetizada do zero (sem samples de terceiros).
130 BPM, Fá# menor: cowbell melódico, 808 com glide e distorção, kick, clap, hi-hats com rolos, textura de vinil.
O primeiro tempo forte do drop cai em DROP (s) do vídeo. Saída: music.wav (48 kHz, estéreo)."""
import numpy as np, wave, math
SR = 48000; BPM = 130; BEAT = 60 / BPM; BAR = BEAT * 4; STEP = BEAT / 4
DUR = 124.7; DROP = 0.68
T0 = DROP - BAR                 # o arquivo começa 1 compasso antes do drop (cowbell sozinho)
N = int((DUR - T0 + 2) * SR)
L = np.zeros(N); R = np.zeros(N)
rng = np.random.default_rng(7)

def add(sig, t, pan=0.0, g=1.0):
    i = int((t - T0) * SR)
    if i >= N or i + len(sig) <= 0: return
    a = max(0, -i); i = max(0, i); n = min(len(sig) - a, N - i)
    L[i:i + n] += sig[a:a + n] * g * (1 - max(0, pan)); R[i:i + n] += sig[a:a + n] * g * (1 + min(0, pan))

def tvec(d): return np.arange(int(d * SR)) / SR

def cowbell(semi, d=0.32):
    t = tvec(d); k = 2 ** (semi / 12)
    f1, f2 = 587 * k, 845 * k
    s = np.sign(np.sin(2 * np.pi * f1 * t)) * 0.5 + np.sign(np.sin(2 * np.pi * f2 * t)) * 0.5
    env = np.exp(-t * 11) * (1 - np.exp(-t * 900))
    s = s * env
    # passa-banda simples: diferença de dois passa-baixas
    def lp(x, a):
        y = np.zeros_like(x); p = 0.0
        for i in range(len(x)): p += a * (x[i] - p); y[i] = p
        return y
    return (lp(s, 0.35) - lp(s, 0.04)) * 0.9

def k808(f, d, glide_to=None):
    t = tvec(d)
    fr = f if glide_to is None else f + (glide_to - f) * np.clip((t - d * 0.55) / (d * 0.25), 0, 1)
    ph = 2 * np.pi * np.cumsum(fr * (1 + 1.6 * np.exp(-t * 40))) / SR
    s = np.sin(ph) * np.exp(-t * 1.1) * (1 - np.exp(-t * 600))
    return np.tanh(s * 3.2) * 0.8

def kick():
    t = tvec(0.35); ph = 2 * np.pi * np.cumsum(48 + 140 * np.exp(-t * 28)) / SR
    return np.tanh(np.sin(ph) * np.exp(-t * 9) * 2.5) * 0.9

def clap():
    t = tvec(0.28); n = rng.standard_normal(len(t))
    env = np.exp(-t * 18) + 0.6 * np.exp(-((t - 0.012) ** 2) / 1e-5) + 0.5 * np.exp(-((t - 0.024) ** 2) / 1e-5)
    body = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30) * 0.5
    hp = n - np.convolve(n, np.ones(6) / 6, 'same')
    return (hp * env * 0.7 + body) * 0.8

def hat(d=0.045, g=1.0):
    t = tvec(d); n = rng.standard_normal(len(t))
    hp = n - np.convolve(n, np.ones(3) / 3, 'same')
    return hp * np.exp(-t * 90) * 0.35 * g

CB = {s: cowbell(s) for s in range(-12, 13)}
KICK, CLAP = kick(), clap()
ROOT = 46.25  # Fá#1
PROG = [0, 0, -4, -2]   # i, i, VI, VII (em semitons)
# riff de cowbell, 16 passos, em semitons a partir de Fá#
RIFF = [0, None, 3, None, 7, None, 5, 3, 0, None, 3, None, 10, 7, 5, None]
RIFF2 = [0, None, 3, None, 7, None, 8, 7, 5, None, 3, None, 2, 3, 5, None]

def bars():
    b = 0
    while T0 + b * BAR < DUR + 1: yield b, T0 + b * BAR; b += 1

for b, tb in bars():
    drums = b >= 1                       # drop no compasso 1 (= DROP)
    section = (b - 1) // 8 if b >= 1 else -1
    riff = RIFF if section % 2 == 0 else RIFF2
    semi_root = PROG[(b - 1) % 4] if b >= 1 else 0
    for k, n in enumerate(riff):
        if n is None: continue
        add(CB[max(-12, min(12, n + semi_root))], tb + k * STEP, pan=(-0.25 if k % 2 else 0.25), g=0.55)
        add(CB[max(-12, min(12, n + semi_root))] * 0.35, tb + k * STEP + STEP * 3, pan=(0.4 if k % 2 else -0.4), g=0.3)  # eco
    if not drums: continue
    f = ROOT * 2 ** (semi_root / 12)
    nxt = ROOT * 2 ** (PROG[b % 4] / 12)
    add(k808(f, BEAT * 2.4), tb, g=0.75)
    add(k808(f, BEAT * 1.4, glide_to=nxt * 2), tb + BEAT * 2.5, g=0.6)
    for s in (0, 6, 10):
        add(KICK, tb + s * STEP, g=0.75)
    for bt in (1, 3):
        add(CLAP, tb + bt * BEAT, g=0.7)
    for s in range(16):
        add(hat(), tb + s * STEP * 2 / 2, pan=0.15, g=0.8 if s % 2 == 0 else 0.5)
    if b % 2 == 1:   # rolo de hi-hat em 1/32 no fim do compasso
        for r in range(8):
            add(hat(0.03, 0.6 + 0.05 * r), tb + BEAT * 3.5 + r * STEP / 2, pan=0.15)

# textura de vinil
vin = rng.standard_normal(N) * 0.004
crk = (rng.random(N) > 0.99993) * rng.standard_normal(N) * 0.25
L += vin + crk; R += vin + crk
mix = np.stack([L, R], 1)
mix = np.tanh(mix * 1.15) / np.tanh(1.15)
mix /= np.max(np.abs(mix)) + 1e-9
mix *= 0.89
# corta para começar no tempo 0 do vídeo
mix = mix[int(-T0 * SR):int((-T0 + DUR) * SR)]
fade = int(1.5 * SR); mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
d = (mix * 32767).astype(np.int16)
w = wave.open('music.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(d.tobytes()); w.close()
print('ok', len(mix) / SR)

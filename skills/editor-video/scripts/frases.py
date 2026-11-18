#!/usr/bin/env python3
"""Segmenta o áudio em frases pela energia e transcreve CADA frase isolada (camada literal).
Isso revela repetições e falsas largadas que o Whisper global esconde.
Uso: frases.py PASTA [--limiar -50] [--junta 0.15] [--modelo medium] [--lang pt] [--inicio 0]
Saída: PASTA/frases.json  [{i, s, e, t}]  e a lista impressa."""
import argparse, json, wave
from pathlib import Path
import numpy as np
from faster_whisper import WhisperModel

ap = argparse.ArgumentParser(); ap.add_argument("pasta")
ap.add_argument("--limiar", type=float, default=-50); ap.add_argument("--junta", type=float, default=0.15)
ap.add_argument("--modelo", default="medium"); ap.add_argument("--lang", default="pt")
ap.add_argument("--inicio", type=float, default=0, help="ignora tudo antes deste segundo (ex.: preparação antes da fala)")
ap.add_argument("--prompt", default="Ãh, é, ele, ele vai, ele vai gastar.", help="initial_prompt com disfluências")
a = ap.parse_args(); work = Path(a.pasta)
E = np.load(work / "env.npy"); v = E > a.limiar
runs = []; k = 0
while k < len(v):
    if v[k]:
        j = k
        while j < len(v) and v[j]: j += 1
        if j - k >= 4: runs.append([k, j])   # >= 40 ms
        k = j
    else: k += 1
ch = []
for r in runs:
    if ch and r[0] - ch[-1][1] < a.junta * 100: ch[-1][1] = r[1]
    else: ch.append(r)
ch = [c for c in ch if c[0] >= a.inicio * 100]
w = wave.open(str(work / "audio.wav")); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
m = WhisperModel(a.modelo, device="cpu", compute_type="int8")
out = []
for i, (s0, e0) in enumerate(ch):
    s, e = s0 / 100, e0 / 100
    seg, _ = m.transcribe(x[int(max(s - .05, 0) * 16000):int((e + .05) * 16000)], language=a.lang, initial_prompt=a.prompt,
                          condition_on_previous_text=False, vad_filter=False, beam_size=5)
    t = " ".join(z.text.strip() for z in seg)
    out.append({"i": i, "s": round(s, 2), "e": round(e, 2), "t": t}); print(i, "%.2f-%.2f" % (s, e), t, flush=True)
json.dump(out, open(work / "frases.json", "w"), ensure_ascii=False, indent=0)

#!/usr/bin/env python3
"""Extrai o áudio (mono 16 kHz) e o envelope de energia em dBFS, janelas de 10 ms.
Uso: energia.py VIDEO PASTA_DE_TRABALHO
Saída: PASTA/audio.wav, PASTA/env.npy e os percentis de energia, para calibrar o limiar de voz."""
import subprocess, sys, wave
from pathlib import Path
import numpy as np

video, work = sys.argv[1], Path(sys.argv[2]); work.mkdir(parents=True, exist_ok=True)
wav = work / "audio.wav"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-ac", "1", "-ar", "16000", str(wav)], check=True)
w = wave.open(str(wav)); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768
h = 160; n = len(x) // h
env = 20 * np.log10(np.sqrt((x[:n * h].reshape(n, h) ** 2).mean(1)) + 1e-9)
np.save(work / "env.npy", env)
print("duração %.1fs | percentis 5/20/50/80/95:" % (len(x) / 16000), [round(float(np.percentile(env, p)), 1) for p in (5, 20, 50, 80, 95)])
print("Limiar de voz de referência: -50 dBFS (fala ~ -20 a -40, silêncio ~ -70 a -80). Ajuste se o ruído de sala for maior.")

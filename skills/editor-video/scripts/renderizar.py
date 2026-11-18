#!/usr/bin/env python3
"""Renderiza a decupagem: corta cada take, reenquadra pelo rosto, concatena, aplica velocidade e master de áudio.
Uso: renderizar.py VIDEO PASTA SAIDA.mp4 [--saida 1080x1920] [--vel 1.2] [--lut arquivo.cube] [--zoom 1.1] [--limite N]
  --saida  proporção/tamanho do quadro final do vídeo falado (padrão 1080x1920, vertical)
  --limite renderiza só os N primeiros cortes (teste rápido)
Rosto: Haar (OpenCV, frontal e perfil), mediana de 3 quadros por take; rosto centralizado a 52% da altura do recorte."""
import argparse, json, subprocess, tempfile
from pathlib import Path
import cv2, numpy as np

ap = argparse.ArgumentParser(); ap.add_argument("video"); ap.add_argument("pasta"); ap.add_argument("saida_mp4")
ap.add_argument("--saida", default="1080x1920"); ap.add_argument("--vel", type=float, default=1.0)
ap.add_argument("--lut"); ap.add_argument("--zoom", type=float, default=1.1); ap.add_argument("--limite", type=int)
ap.add_argument("--loudness", type=float, default=-13)
a = ap.parse_args(); work = Path(a.pasta); OW, OH = map(int, a.saida.split("x"))
segs = json.load(open(work / "cortes.json"))["segs"][: a.limite]

def run(*c): subprocess.run(list(map(str, c)), check=True)
pr = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=width,height:stream_side_data=rotation",
                     "-of", "json", a.video], capture_output=True, text=True, check=True)
st = json.loads(pr.stdout)["streams"][0]; W, H = st["width"], st["height"]
rot = int(round(abs((st.get("side_data_list") or [{}])[0].get("rotation", 0)))) % 180
if rot == 90: W, H = H, W   # ffmpeg autorrotaciona

fc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
pc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_profileface.xml")
def rosto(t0, t1, tmp):
    boxes = []
    for k, f in enumerate((.2, .5, .8)):
        p = Path(tmp) / f"f{k}.jpg"
        run("ffmpeg", "-v", "error", "-y", "-ss", t0 + (t1 - t0) * f, "-i", a.video, "-frames:v", 1, "-vf", "scale=540:-1", p)
        g = cv2.cvtColor(cv2.imread(str(p)), cv2.COLOR_BGR2GRAY); sc = W / g.shape[1]; cand = []
        for c, flip in ((fc, 0), (pc, 0), (pc, 1)):
            im = cv2.flip(g, 1) if flip else g
            for (x, y, w, h) in c.detectMultiScale(im, 1.1, 6, minSize=(g.shape[1] // 5, g.shape[1] // 5)):
                if flip: x = g.shape[1] - x - w
                cand.append((w * h, x, y, w, h))
        if cand: boxes.append(max(cand)[1:])
    return list(np.median(np.array(boxes), 0) * sc) if boxes else None

# caixa base: maior retângulo na proporção da saída dentro do quadro
ar = OW / OH; bw, bh = (W, W / ar) if W / ar <= H else (H * ar, H)
tmp = tempfile.mkdtemp(); parts = []; last = None
for i, s in enumerate(segs):
    t0, t1 = s["src"]; d = round(t1 - t0, 4)
    f = rosto(t0, t1, tmp) or last; last = f
    z = a.zoom if s["zoom"] else 1.0; cw, ch = bw / z, bh / z
    cx, cy = (f[0] + f[2] / 2, f[1] + f[3] / 2) if f else (W / 2, H / 2)
    x0 = int(min(max(cx - cw / 2, 0), W - cw)); y0 = int(min(max(cy - .52 * ch, 0), H - ch))
    vf = ([f"lut3d={a.lut}"] if a.lut else []) + [f"crop={int(cw)}:{int(ch)}:{x0}:{y0}", f"scale={OW}:{OH}:flags=lanczos", "fps=30", "format=yuv420p"]
    p = work / f"take_{i:03d}.mov"
    run("ffmpeg", "-v", "error", "-y", "-ss", t0, "-i", a.video, "-t", d, "-vf", ",".join(vf),
        "-af", f"afade=t=in:d=0.01,afade=t=out:st={max(0, d - .015)}:d=0.015", "-c:v", "libx264", "-crf", 14, "-preset", "fast",
        "-c:a", "pcm_s16le", "-ar", 48000, "-ac", 2, p); parts.append(p)
lst = work / "concat.txt"; lst.write_text("".join(f"file '{p.resolve()}'\n" for p in parts))
run("ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", 0, "-i", lst, "-c", "copy", work / "falado_1x.mov")
v = a.vel
af = (f"atempo={v}," if v != 1 else "") + ("highpass=f=80,equalizer=f=120:t=q:w=1:g=2,equalizer=f=250:t=q:w=1.2:g=-2.5,"
      "equalizer=f=3500:t=q:w=1:g=3,highshelf=f=10000:g=2,acompressor=threshold=-22dB:ratio=3.5:attack=5:release=90:makeup=4,"
      f"loudnorm=I={a.loudness}:TP=-1.5:LRA=7,alimiter=limit=0.8:level=disabled")
run("ffmpeg", "-v", "error", "-y", "-i", work / "falado_1x.mov", "-vf", f"setpts=PTS/{v},fps=30", "-af", af, "-ar", 48000,
    "-c:v", "libx264", "-crf", 18, "-preset", "medium", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", a.saida_mp4)
m = subprocess.run(["ffmpeg", "-hide_banner", "-i", a.saida_mp4, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
print([l.strip() for l in m.splitlines() if "I:" in l or "Peak:" in l][-2:])
print("OK", a.saida_mp4)

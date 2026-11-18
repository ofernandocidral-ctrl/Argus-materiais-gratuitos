"""Recorte do apresentador quadro a quadro (v0.19): rembg em CPU, máscara em meia resolução, RGBA em cutf/%05d.png.
Uso: python3 cutout.py video.mp4 cutf [parte n_partes] [--ranges ranges.txt]
Rode 3 processos em paralelo (0 3, 1 3, 2 3) com nohup e < /dev/null. Medido no exemplo: ~1,5 quadro/s no total.
--ranges: arquivo com lista Python [(ini, fim), ...] de quadros; sem ele, recorta o vídeo inteiro."""
import cv2, os, sys, ast, numpy as np
from rembg import remove, new_session
from PIL import Image
video, outdir = sys.argv[1], sys.argv[2]
part, n = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 and sys.argv[3].isdigit() else (0, 1)
os.makedirs(outdir, exist_ok=True)
cap = cv2.VideoCapture(video)
total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
R = ast.literal_eval(open(sys.argv[sys.argv.index('--ranges') + 1]).read()) if '--ranges' in sys.argv else [(0, total)]
if '--ranges' not in sys.argv:   # divide o vídeo inteiro em fatias para os processos paralelos
    step = 300; R = [(a, min(a + step, total)) for a in range(0, total, step)]
s = new_session('u2net_human_seg', providers=['CPUExecutionProvider'])   # CoreML falhou no meio do exemplo
for a, b in R[part::n]:
    cap.set(cv2.CAP_PROP_POS_FRAMES, a)
    for i in range(a, b):
        ok, fr = cap.read()
        if not ok: break
        o = os.path.join(outdir, '%05d.png' % i)
        if os.path.exists(o): continue
        sm = cv2.resize(fr, (fr.shape[1] // 2, fr.shape[0] // 2), interpolation=cv2.INTER_AREA)
        m = np.asarray(remove(Image.fromarray(cv2.cvtColor(sm, cv2.COLOR_BGR2RGB)), session=s, only_mask=True))
        m = cv2.resize(m, (fr.shape[1], fr.shape[0]), interpolation=cv2.INTER_LINEAR)
        cv2.imwrite(o + '.tmp.png', np.dstack([fr, m])); os.rename(o + '.tmp.png', o)   # gravação atômica
print('ok')

"""Composição final: tela de baixo (decupagem) + quadros do motion + SFX -> MP4 1080x1920.
Uso: python3 compor.py W BAIXO.mov SAIDA.mp4 [--sfxdir DIR] [--cheio CHEIO.mov]
- Se W/layout.json existir (motion_layout), alterna tela dividida, cartão e rosto em tela cheia (este exige --cheio).
- W: pasta de trabalho com quadros/ e sfx.json (render_motion.py)
- BAIXO.mov: vídeo falado 1080x960 já com cortes, velocidade e master (renderizar.py --saida 1080x960)
"""
import json, os, sys, subprocess
W, BAIXO, SAIDA = sys.argv[1], sys.argv[2], sys.argv[3]
SFXDIR = sys.argv[sys.argv.index('--sfxdir') + 1] if '--sfxdir' in sys.argv else os.path.join(W, 'sfx')
ev = json.load(open(os.path.join(W, 'sfx.json')))
dur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', BAIXO]).decode())
CHEIO = sys.argv[sys.argv.index('--cheio') + 1] if '--cheio' in sys.argv else None
lay_path = os.path.join(W, 'layout.json')
LAY = json.load(open(lay_path)) if os.path.exists(lay_path) else []
usa_modos = any(l['modo'] != 'split' for l in LAY)
args = ['ffmpeg', '-v', 'error', '-y', '-i', BAIXO, '-framerate', '30', '-i', os.path.join(W, 'quadros', '%05d.png')]
n_in = 2
if usa_modos:
    if any(l['modo'] == 'rosto' for l in LAY) and not CHEIO:
        sys.exit('layout.json tem modo rosto: passe --cheio VIDEO_1080x1920 (renderizar.py --saida 1080x1920)')
    if CHEIO: args += ['-i', CHEIO]; n_in = 3
fl = []; lab = ''
for k, (t, name, g) in enumerate(ev):
    args += ['-i', os.path.join(SFXDIR, f'{name}.wav')]; ms = int(max(0, t) * 1000)
    fl.append(f'[{k + n_in}:a]volume={g}dB,adelay={ms}|{ms}[s{k}]'); lab += f'[s{k}]'
if not usa_modos:
    fc = '[0:v]pad=1080:1920:0:960:color=0xF0EEEA[b];[b][1:v]overlay=0:0:eof_action=repeat,format=yuv420p[v];'
else:
    def en(modo):
        e = '+'.join(f"between(t,{l['s']:.3f},{l['e'] - 0.0005:.4f})" for l in LAY if l['modo'] == modo)
        return e or '0'
    # modos: split = vídeo embaixo; cartao = vídeo num cartão 820x820 em (130,1010); rosto = vídeo em tela cheia
    fc = (f"color=c=0xF0EEEA:s=1080x1920:r=30:d={dur:.3f}[bg];[0:v]split=2[va][vb];"
          f"[vb]crop=960:960:60:0,scale=820:820:flags=lanczos[vc];"
          f"[bg][va]overlay=0:960:enable='{en('split')}'[b1];[b1][vc]overlay=130:1010:enable='{en('cartao')}'[b2];")
    if CHEIO:
        fc += f"[b2][2:v]overlay=0:0:enable='{en('rosto')}'[b3];"
    else:
        fc += '[b2]null[b3];'
    fc += '[b3][1:v]overlay=0:0:eof_action=repeat,format=yuv420p[v];'
if ev:
    fc += ';'.join(fl) + f';{lab}amix=inputs={len(ev)}:normalize=0[sx];[0:a][sx]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.84:level=disabled[a]'
else:
    fc += '[0:a]anull[a]'
args += ['-filter_complex', fc, '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-profile:v', 'high',
         '-pix_fmt', 'yuv420p', '-r', '30', '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-movflags', '+faststart', '-t', f'{dur:.3f}', SAIDA]
subprocess.run(args, check=True)
r = subprocess.run(['ffmpeg', '-hide_banner', '-i', SAIDA, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
print('\n'.join(l.strip() for l in r.splitlines() if l.strip().startswith(('I:', 'Peak:')))[-60:])
print('OK', SAIDA)

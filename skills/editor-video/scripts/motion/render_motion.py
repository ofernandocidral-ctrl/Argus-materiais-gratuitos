"""Renderiza os quadros do painel de cima (motion + legenda) a partir de um arquivo de cenas.
Uso: W=<pasta> DUR=<s> python3 render_motion.py CENAS.py [--preview t1 t2 ...] [--workers 8]
Saída: <W>/quadros/%05d.png (1080x1920 RGBA, painel de cima opaco, resto transparente) e <W>/sfx.json.
"""
import os, sys, json, math, importlib.util
from multiprocessing import Pool
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

cenas_path = sys.argv[1]
spec = importlib.util.spec_from_file_location('cenas', cenas_path)
C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)
import motion_lib as M
OUT = os.path.join(os.environ.get('W', '.'), 'quadros')

def frame(i):
    t = i / M.FPS
    if hasattr(M, 'render_frame'):          # motion_layout.configure() instalado: quadro por modo de layout
        out = M.render_frame(t)
    else:
        out = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0))
        top = M.render_top(C.SC, t)
        M.caption_layer(t, top)
        out.paste(top, (0, 0))
    out.save(os.path.join(OUT, f'{i:05d}.png'), compress_level=1)
    return i

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    args = sys.argv[2:]
    if args and args[0] == '--preview':
        for tt in map(float, args[1:]):
            frame(int(tt * M.FPS)); print(os.path.join(OUT, '%05d.png' % int(tt * M.FPS)))
        sys.exit()
    workers = int(args[args.index('--workers') + 1]) if '--workers' in args else 8
    n = int(math.ceil(M.DUR * M.FPS))
    json.dump(sorted(getattr(C, 'SFX', [])), open(os.path.join(os.environ.get('W', '.'), 'sfx.json'), 'w'))
    if hasattr(M, 'render_frame'):
        import motion_layout; motion_layout.export_layout(os.path.join(os.environ.get('W', '.'), 'layout.json'))
    with Pool(workers) as pool:
        for k, _ in enumerate(pool.imap_unordered(frame, range(n), chunksize=10)):
            if k % 500 == 0: print(k, '/', n, flush=True)
    print('quadros', n)

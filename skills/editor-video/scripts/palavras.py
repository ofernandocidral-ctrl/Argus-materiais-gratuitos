"""Tempos por palavra no áudio do vídeo FINAL (depois de cortes e velocidade), para motion e legenda.
Uso: python3 palavras.py BAIXO.mov W [--prompt "Claude, MCP, Meta"] [--fix '{"Cloud":"Claude"}']
Saída: W/palavras.json [{w, s, e}] e W/palavras.txt (palavra@tempo) para consulta.
Revise palavras.txt: o Whisper erra nomes próprios; corrija via --fix (troca exata de palavra).
"""
import json, os, sys, subprocess
src, W = sys.argv[1], sys.argv[2]
prompt = sys.argv[sys.argv.index('--prompt') + 1] if '--prompt' in sys.argv else None
fix = json.loads(sys.argv[sys.argv.index('--fix') + 1]) if '--fix' in sys.argv else {}
wav = os.path.join(W, 'final16.wav')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-ac', '1', '-ar', '16000', wav], check=True)
from faster_whisper import WhisperModel
m = WhisperModel('medium', device='cpu', compute_type='int8')
segs, _ = m.transcribe(wav, language='pt', word_timestamps=True, condition_on_previous_text=False, initial_prompt=prompt)
Wd = [{'w': fix.get(w.word.strip(), w.word.strip()), 's': round(w.start, 3), 'e': round(w.end, 3)} for s in segs for w in s.words]
for i, w in enumerate(Wd):   # junta "%" solto à palavra anterior
    if w['w'] in ('%', '%.', '%,') and i:
        Wd[i - 1]['w'] += w['w']; Wd[i - 1]['e'] = w['e']; w['skip'] = 1
Wd = [w for w in Wd if not w.get('skip')]
json.dump(Wd, open(os.path.join(W, 'palavras.json'), 'w'), ensure_ascii=False)
open(os.path.join(W, 'palavras.txt'), 'w').write(' '.join(f"{w['w']}@{w['s']:.1f}" for w in Wd))
print('OK', len(Wd), 'palavras ->', os.path.join(W, 'palavras.json'))

#!/usr/bin/env python3
"""Monta a lista de cortes a partir da ESCOLHA DE TAKES (decisão revisada por humano/modelo).
takes.json: lista de {"frase": N, "ini": seg_opcional, "fim": seg_opcional, "texto": "legenda/anotação opcional"}
  - 'frase' = índice em frases.json. 'ini'/'fim' sobrescrevem o corte quando a regra de energia não basta
    (ex.: respiração colada ao fim da frase).
Uso: montar.py PASTA [--pre 0.03] [--pos 0.06] [--fps 30] [--salto 1.0]
Regras: respiro de 30 ms antes e 60 ms depois da voz; duração alinhada a frames inteiros; o enquadramento
(zoom) só alterna quando o corte salta mais de --salto segundos no bruto (troca real de take).
Saída: PASTA/cortes.json e tabela impressa."""
import argparse, json
from pathlib import Path

ap = argparse.ArgumentParser(); ap.add_argument("pasta")
ap.add_argument("--pre", type=float, default=0.03); ap.add_argument("--pos", type=float, default=0.06)
ap.add_argument("--fps", type=int, default=30); ap.add_argument("--salto", type=float, default=1.0)
a = ap.parse_args(); work = Path(a.pasta)
F = {f["i"]: f for f in json.load(open(work / "frases.json"))}
T = json.load(open(work / "takes.json"))
out = []; t = 0.0; prev = None; zoom = 0
for tk in T:
    f = F[tk["frase"]]
    s = tk["ini"] if tk.get("ini") is not None else f["s"] - a.pre
    e = (tk["fim"] + 0.02) if tk.get("fim") is not None else f["e"] + a.pos
    d = round(round((e - s) * a.fps) / a.fps, 4)
    if prev is not None and s - prev > a.salto: zoom ^= 1
    out.append({"frase": tk["frase"], "src": [round(s, 3), round(s + d, 4)], "dst": [round(t, 4), round(t + d, 4)],
                "zoom": zoom, "texto": tk.get("texto") or f["t"]})
    t += d; prev = s + d
json.dump({"segs": out, "dur": round(t, 3)}, open(work / "cortes.json", "w"), ensure_ascii=False, indent=0)
print("| # | saída | bruto | zoom | texto |\n|---|---|---|---|---|")
for i, o in enumerate(out):
    print("| %d | %d:%05.2f | %d:%05.2f | %d | %s |" % (i + 1, o["dst"][0] // 60, o["dst"][0] % 60, o["src"][0] // 60, o["src"][0] % 60, o["zoom"], o["texto"][:70]))
print("duração sem velocidade: %.1fs, %d cortes, %d trocas de zoom" % (t, len(out), sum(1 for x, y in zip(out, out[1:]) if x["zoom"] != y["zoom"])))

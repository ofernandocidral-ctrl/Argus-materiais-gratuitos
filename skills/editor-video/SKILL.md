---
name: editor-video
description: Edição de vídeos falados para Reels e redes sociais, do bruto ao arquivo final, com scripts de decupagem, legenda, SFX e motion em Python.
---

# Editor de vídeo (skill genérica)

Conjunto de scripts para editar vídeos falados. Cada script faz uma etapa e pode ser usado sozinho.

## Estrutura

- `scripts/`: etapas do pipeline (legenda por palavra, decupagem, SFX, cores, montagem e render).
- `scripts/motion/`: módulos de motion graphics (camada de texto, mascote em pixel art e recorte de pessoa).
- `assets/fonts/`: Inter e Instrument Serif, ambas com licença aberta (OFL).

## Como usar

1. Coloque o vídeo bruto numa pasta de trabalho.
2. Rode a transcrição e a decupagem para gerar os cortes.
3. Gere as legendas por palavra e aplique o motion, se for usar.
4. Renderize o arquivo final.

Os sons de efeito e os vídeos de referência não estão incluídos. Use os seus próprios arquivos, com licença de uso.

## Limites

- Os caminhos de entrada e saída são passados como argumento. Não há caminhos fixos.
- Os exemplos de motion foram removidos. Os módulos continuam funcionando, mas sem roteiro de exemplo.

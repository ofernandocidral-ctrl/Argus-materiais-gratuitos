# Claude no seu computador: guia prático

Aprenda a usar o **Claude Code** para ler, organizar, criar e editar arquivos do seu computador usando linguagem natural.

> **Atenção:** o Claude no navegador não recebe acesso automático aos arquivos locais. Este tutorial usa o Claude Code, instalado no computador, e as permissões concedidas por você.

## 1. Antes de começar

Você precisa de um computador com macOS, Windows ou Linux, conexão com a internet, terminal e uma conta com acesso ao Claude Code (por assinatura ou API, conforme seu plano). Comece com uma pasta de teste, sem arquivos importantes.

Documentação oficial: https://code.claude.com/docs/en/overview

## 2. Instalação

Abra o guia oficial para instalar o Claude Code no seu sistema:

https://code.claude.com/docs/en/setup

Depois de instalar, confirme no terminal:

```bash
claude --version
```

Não execute scripts de instalação encontrados em fontes desconhecidas.

## 3. Crie uma pasta de teste

**macOS / Linux:**

```bash
mkdir -p ~/claude-teste
cd ~/claude-teste
```

**Windows (PowerShell):**

```powershell
New-Item -ItemType Directory -Force "$HOME\claude-teste"
Set-Location "$HOME\claude-teste"
```

Coloque nessa pasta alguns arquivos de exemplo, sem informações pessoais ou confidenciais.

## 4. Abra o Claude Code

Dentro da pasta, execute:

```bash
claude
```

Siga as instruções de autenticação. O Claude Code trabalhará com o contexto da pasta aberta, mas **não presuma que o acesso esteja restrito a ela**: ferramentas e permissões podem permitir acesso a outros caminhos.

## 5. Cinco prompts prontos

### 1 — Entender seus arquivos

> Analise os arquivos desta pasta e explique como estão organizados. Não altere nada.

### 2 — Organizar documentos

> Proponha uma estrutura de pastas mais organizada. Antes de mover ou excluir qualquer arquivo, apresente um plano e aguarde minha aprovação.

### 3 — Gerar um resumo

> Leia os arquivos de texto desta pasta e crie um RESUMO.md com os principais assuntos, sem incluir informações sensíveis.

### 4 — Padronizar nomes

> Identifique nomes de arquivos inconsistentes e sugira uma padronização. Mostre a lista de alterações antes de renomear qualquer arquivo.

### 5 — Criar a estrutura de um projeto

> Planeje uma estrutura inicial de projeto com README.md, docs/ e exemplos/. Mostre o plano antes de criar os arquivos.

## 6. Cuidados importantes

- Faça backup antes de alterações em lote.
- Peça uma prévia e aprove as alterações antes da execução.
- Nunca compartilhe senhas, tokens, arquivos .env ou dados confidenciais.
- Revise comandos de terminal, instalações e operações de exclusão.
- Não desative verificações de permissão para acelerar tarefas.
- Em projetos com Git, revise o `git diff` antes de confirmar mudanças.

## 7. Problemas comuns

**`claude: command not found`:** confira se a instalação foi concluída e se o executável está no PATH.

**Erro ao autenticar:** verifique sua conta e o acesso ao Claude Code.

**Arquivo não encontrado:** confira o caminho, a pasta atual e as permissões.

**Medo de perder dados:** comece com análise somente leitura e faça edições pequenas, com backup.

## 8. Próximo passo

Quando estiver confortável, abra uma pasta real de trabalho, peça ao Claude para mapear os arquivos **sem modificá-los** e avance gradualmente para edições supervisionadas.

**Documentação oficial:** [Visão geral](https://code.claude.com/docs/en/overview) · [Instalação](https://code.claude.com/docs/en/setup) · [Permissões](https://code.claude.com/docs/en/permissions)

---

Material educativo gratuito e independente. Claude e Claude Code são produtos da Anthropic; não há afiliação com a empresa.

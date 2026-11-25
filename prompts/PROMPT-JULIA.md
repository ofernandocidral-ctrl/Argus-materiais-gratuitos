# Prompt: como montar uma gerente de projetos com IA (Júlia)

Isca do VD-006, "Criei uma gestora de projetos com IA". Quem comentar **Júlia** recebe este prompt.

Status: rascunho, não publicado e não testado com o ManyChat. Publicação e ativação dependem de aprovação do Fernando.

## Para que serve

Este prompt ensina o Claude ou o Codex a montar um agente que faz o papel de gerente de projetos da sua operação: recebe pedidos, lança demandas, acompanha o andamento, analisa o resultado e registra tudo em uma pasta de entrada, para que o agente aprenda o seu jeito de trabalhar.

Ele funciona em cinco fases. Cada fase termina com uma pergunta para você. Só avance depois de responder.

## Fase 1: Entender a operação

Antes de montar qualquer coisa, pergunte e anote:

1. Quais ferramentas de IA você usa no dia a dia (por exemplo: Claude Code, Codex, Antigravity)?
2. Onde ficam os seus documentos (um cofre de notas, uma pasta, um gerenciador de tarefas)?
3. Quantas pessoas e agentes trabalham com você, e quem decide o quê?
4. Qual é o tipo de pedido que mais se repete?

Resuma em uma lista curta e peça confirmação antes de seguir.

## Fase 2: Definir o papel da gerente

Escreva a descrição do agente com:

- **Função:** receber pedidos, transformar cada um em uma demanda com objetivo, responsável e critério de conclusão, e acompanhar até o fim.
- **O que ela pode decidir sozinha:** classificar, organizar e sugerir prioridade.
- **O que ela precisa perguntar antes:** qualquer mudança de escopo, gasto, envio externo ou publicação.
- **Como ela responde:** o formato que você prefere, com resumo primeiro e detalhes depois.

Mostre a descrição e peça ajustes.

## Fase 3: Criar a pasta de entrada e a diretriz

1. Crie uma pasta chamada **Inbox** dentro da sua base de documentos.
2. Escreva um arquivo de instruções (chamado `cloud.md` ou `AGENTS.md`, conforme a ferramenta) com a regra: **toda conversa iniciada nesta base precisa ser registrada no Inbox**, com data, ferramenta, pedido e resultado.
3. Adapte o arquivo para cada ferramenta que você usa, para que a regra valha em todas elas.

Confirme que a pasta e o arquivo existem e que a regra está escrita antes de seguir.

## Fase 4: Criar a rotina diária

Configure uma análise diária, de preferência às 7h, com esta instrução:

> Analise tudo o que foi registrado no Inbox nas últimas 24 horas. Liste as alterações pedidas, as decisões tomadas, as pendências e as fontes usadas. Aponte o que mudou no seu perfil de pedidos e no seu jeito de decidir. Não tome decisões por conta própria: registre sugestões e espere aprovação.

Essa rotina é o que faz a gerente ficar mais precisa com o tempo. Ela lê o histórico e ajusta o entendimento do seu perfil.

## Fase 5: Testar e liberar

1. Peça uma demanda fictícia, com começo, meio e fim. Por exemplo: "Organize o lançamento de um produto em três etapas".
2. Confira se a gerente criou a demanda com objetivo, responsável, prazo e critério de conclusão.
3. Confira se o registro apareceu no Inbox.
4. Corrija o que faltou e repita o teste.
5. Só libere a rotina diária depois que o teste passar e você aprovar o resultado.

## O que não fazer

- Não deixe a gerente publicar, enviar mensagens ou alterar contas de terceiros sem aprovação.
- Não coloque senhas, chaves de acesso ou dados pessoais de clientes no Inbox.
- Não confie na memória de uma ferramenta para outra. O que vale é o que está registrado no Inbox e nas instruções.

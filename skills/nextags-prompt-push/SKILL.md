---
name: nextags-prompt-push
description: "Sobe/atualiza SÓ o prompt de um agente de IA no IA Hub da NexTags direto pela API (POST /api/agents/{id} com {\"prompt\": ...}), sem tocar em modelo, tokens, raciocínio ou prioridade. Use quando o usuário pedir pra colar/subir/trocar/atualizar o prompt de um agente: 'cola na Bia esse prompt', 'sobe esse prompt na Ui Vendas', 'atualiza o prompt do SAC', 'joga esse prompt no roteador', 'coloca no IA Hub', 'manda esse prompt pro agente'. Também serve pra baixar/fazer backup do prompt atual de um agente. NÃO cria agente (a API não tem rota de criação) e NÃO configura modelo."
metadata:
  type: reference
---

# NexTags — subir prompt no IA Hub

Troca o prompt de um agente que **já existe** no IA Hub da NexTags, sem o usuário precisar abrir o painel e colar.

## Regra de ouro: só o prompt

O corpo do POST é **sempre e só** `{"prompt": "..."}`.

- Nunca mandar `model`, `max_output_tokens` nem nenhum outro campo, nem se o usuário só "sugerir" um modelo. Modelo, tokens, raciocínio e prioridade são configurados pelo usuário no painel. Pode **recomendar**, nunca **aplicar**.
- Motivo: em 23/10/2026, um POST com `model` + `max_output_tokens` deixou o painel carregando infinito. A API ignora `null`, então não dá pra desfazer, e o Roteador e o Revalidador tiveram que ser apagados e recriados.

## API

- Base: `https://app.nextagsai.com.br/api` · header `X-ACCESS-TOKEN: <token da conta>` (valor puro, **não** é Bearer).
- `GET /agents` → lista `{data: [{id, name, ...}]}` (`{"data":[]}` se a conta não tem agente).
- `GET /agents/{id}` → agente com `prompt`, `model`, `aiPriority`...
- `POST /agents/{id}` com `{"prompt": "..."}` → atualiza.
- Não existe rota de criação: o agente tem que ter sido criado no painel antes.

## Trava: agente sem config salva

Se o `GET /agents/{id}` volta só com `id`/`name` (sem `model` e `aiPriority`), o agente foi criado no painel mas **nunca salvo**. POST nele deixa o painel em branco ou quebrado. Nesse caso **não enviar**: pedir pro usuário abrir o agente no IA Hub, salvar a config uma vez, e tentar de novo. O script já aborta sozinho nesse caso.

## Passo a passo

1. **Descobrir a conta e o token.** O token é da conta do cliente (cada cliente tem o seu). Se o usuário não disse de qual cliente é o agente, ou o token dessa conta não está na conversa, **perguntar**. Nunca gravar o token em arquivo da skill, no relatório nem na memória.
2. **Pegar o prompt.**
   - Colado na mensagem ("cola na Bia esse prompt: ...") → gravar o texto **exatamente como veio** num `.md` no scratchpad (não reescrever, não "melhorar", não corrigir nada sem o usuário pedir).
   - Arquivo (ex.: `Documents\WALKERS\<Cliente>\prompt-*.md`) → usar o arquivo direto. Se o arquivo tiver cabeçalho/notas que não fazem parte do prompt (ex.: "versão", "changelog" fora do prompt), perguntar antes de cortar.
3. **Achar o agente** pelo nome que o usuário falou (busca ignora maiúscula e acento; aceita id):
   ```
   python ~/.claude/skills/nextags-prompt-push/scripts/nextags_prompt.py list --token <T>
   ```
   Se mais de um agente bater com o nome, ou nenhum, mostrar a lista e perguntar qual.
4. **Simular** (não envia nada, mostra agente e tamanho atual × novo, e confere a trava):
   ```
   python ~/.claude/skills/nextags-prompt-push/scripts/nextags_prompt.py push --token <T> --agent "Bia" --file <prompt.md>
   ```
5. **Enviar.** O pedido "cola na Bia esse prompt" já é a autorização: não precisa perguntar de novo se o agente e a conta estão claros. Rodar com `--yes` e `--backup-dir` apontando pra pasta do cliente (`Documents\WALKERS\<Cliente>\backups-prompt`), ou pro scratchpad se não houver pasta:
   ```
   python ~/.claude/skills/nextags-prompt-push/scripts/nextags_prompt.py push --token <T> --agent "Bia" --file <prompt.md> --yes --backup-dir "<pasta>"
   ```
   O script salva o prompt antigo antes, faz o POST só com `prompt` e confere com GET que o prompt bateu e o modelo ficou igual.
6. **Responder curto:** agente (nome + id), conta, tamanho antigo → novo, caminho do backup, e o resultado da conferência. Se a conferência falhar, dizer exatamente o que deu diferente; não tentar "consertar" mandando outros campos.

## Desfazer

Pra voltar o prompt anterior, rodar o mesmo `push --yes` usando o arquivo de backup como `--file`.

## Baixar o prompt atual

```
python ~/.claude/skills/nextags-prompt-push/scripts/nextags_prompt.py show --token <T> --agent "Bia" --out <arquivo.md>
```

## Depois de subir

- O prompt vale na hora pros próximos atendimentos. Pra validar ao vivo, usar a skill `nextags-webchat-tester`.
- Se o prompt subido for uma versão nova de um projeto acompanhado na memória, atualizar a memória do cliente com a versão que está no ar.

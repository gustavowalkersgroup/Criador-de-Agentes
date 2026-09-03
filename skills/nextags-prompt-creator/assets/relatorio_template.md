# Relatório de Criação — {NOME_DO_AGENTE} ({NOME_EMPRESA})

**Prompt entregue:** `{ARQUIVO_PROMPT}`
**Data:** {DATA}
**Skill:** nextags-prompt-creator

> Relatório ENXUTO: só o que o humano precisa para subir a operação. Nada de
> estatística de enchimento ("redução de X%", "0 violações", "passou no analyzer").
> Tudo que é meta-doc (pendência, changelog, decisão) mora AQUI, nunca no prompt.

---

## 1. O que foi entregue

| Item | Arquivo / valor |
|---|---|
| Agente | {NOME_AGENTE} — {TIPO: vendas \| SAC \| triagem \| comercial \| misto} |
| Canais | {WhatsApp / Instagram / Messenger / webchat} |
| Prompt do agente | `{ARQUIVO_PROMPT}` |
| Prompt do ROTEADOR | `{ARQUIVO_ROTEADOR}` — *só em projeto com 2+ IAs* |
| Prompt do REVALIDADOR | `{ARQUIVO_REVALIDADOR}` — *só em projeto com 2+ IAs* |
| Tem MCP/tools? | {sim — listar / não (modo estática pura)} |

---

## 2. ⚠️ Pendências críticas (resolver ANTES de subir em produção)

> Cada placeholder que ficou no prompt. Sem isso o agente sobe quebrado ou
> disparando para lugar nenhum.

| Placeholder no prompt | O que falta | Onde conseguir |
|---|---|---|
| `<ID_DO_FLUXO_PIPELINE>` | id do fluxo de transferência para humano | `GET /accounts/flows` na conta do cliente |
| `<ID_DO_FLUXO_NPS>` | id do fluxo de NPS (se houver) | idem |
| `{OUTRO_PLACEHOLDER}` | {o que falta} | {como obter} |

⚠️ Valide todo `flow_id` em `GET /accounts/flows` antes de escrever no prompt:
`/send/{flow_id}` retorna `success:true` até para id inexistente (evidência: Alto
Giro) — id errado falha em silêncio.

---

## 3. Decisões: briefing × site

> Só o que divergiu. Em conflito, o briefing ganha — registre a fonte para o
> cliente conferir.

| Ponto | Briefing diz | Site diz | Decisão | Confirmar? |
|---|---|---|---|---|
| {ex.: frete grátis} | {R$ 199} | {R$ 299} | seguiu o briefing | ✋ sim |

Exceções ao método canônico registradas (se houver):

- {ex.: cliente usa `garantia` como valor extra de `motivo_transferencia` — o fluxo
  precisa do ramo correspondente}
- {ex.: CUFs legados `StatusPedidoBW` mantidos, não renomeados — o fluxo lê esses nomes}

---

## 4. LISTA DE FLUXOS E CAMPOS A CRIAR

> É o entregável mais importante para o cliente montar a operação. Detalhe e
> checklist completos em `references/campos_canonicos.md` §7.

### 4.1 CUFs (campos personalizados) — `POST /accounts/custom_fields {name, type}`

| Campo | Tipo (API) | Quem grava | Precisa? |
|---|---|---|---|
| `setor_agente` | Texto (0) | roteador | {sim se 2+ IAs} |
| `tipo_setor` | Seleção única (6): `humano`, `bot` | revalidador | {sim se 2+ IAs} |
| `motivo_transferencia` | Texto (0) | a IA | sim |
| `prioridade_pipeline` | Seleção única (6): `baixa`, `media`, `alta` | a IA | sim |
| `resumo_pipeline` | Texto (0) | a IA | sim |
| `resposta_ia` | Texto (0) | fluxo (Filtro JSON) | {sim se 2+ IAs} |
| `data_inicial_pipeline` | Data e hora (3) | fluxo de pipeline | sim |
| `data_vencimento` | Data e hora (3) | fluxo de pipeline (SLA) | sim |
| `horario_atendimento` | Texto (0) | fluxo | sim |
| `ultimo_atendimento` | Texto (0) | fluxo | recomendado |
| `nota_nps`, `comentario_nps`, `sugestao`, `data_nps` | Número (1) / Texto (0) / Texto (0) / Data e hora (3) | fluxo de NPS | {se houver NPS} |
| Transacionais (`numero_pedido`, `status_pedido`, `rastreio_url`, …) | todos Texto (0) | n8n | {se houver integração} |

⚠️ Campo que recebe `set_field_value` é tipo **Texto**. Tipo Número descarta o valor
em silêncio (evidência: Mayuí, reincidente em Degan). A API **não tem DELETE** de
custom field — faça dry-run (`GET /accounts/custom_fields` → diff → criar só o que
falta). Token é por conta: token errado retorna 200 e cria na conta errada
(evidência: Wazzu com token da Hebreus Doze).

### 4.2 Tags — `POST /accounts/tags {name}`

```
[ ] prioridade_alta  [ ] prioridade_media  [ ] prioridade_baixa  [ ] humano
[ ] transacional  [ ] Pedido Aprovado  [ ] Pedido Enviado  [ ] Pedido Entregue   (se transacional)
[ ] NPS_enviado  [ ] feedback_positivo  [ ] feedback_neutro  [ ] feedback_negativo (se NPS)
[ ] {tags específicas do cliente}
```

A IA só usa `add_tag` quando o briefing pedir. Tags de prioridade são gravadas pelo
FLUXO, espelhando `prioridade_pipeline`.

### 4.3 Fluxos NexTags

| Fluxo | Papel | flow_id |
|---|---|---|
| ENTRADA (roda em toda mensagem) | roteador grava `setor_agente` → condição por setor → ramo `else` chama o revalidador (arquivar → aguardar 1h → bloquear) | — |
| PIPELINE (UM só) | 00 início / 01 SLA (`data_vencimento` = agora + {SLA}) / 02 transferir para humano / 03 roteia por `motivo_transferencia`, lê `prioridade_pipeline`, comenta `resumo_pipeline` no card | `<ID_DO_FLUXO_PIPELINE>` |
| NPS | pós-atendimento (`nota_nps`, `comentario_nps`, `sugestao`, `data_nps`) | `<ID_DO_FLUXO_NPS>` |
| {Fluxos que o cliente já tem para a IA delegar: catálogo, PDF, coleta complexa} | {propósito} | `{id}` |
| Transacionais no n8n | pedido pago/enviado/entregue, carrinho abandonado | — (skill `nextags-webhook-builder`) |

### 4.4 Prompts entregues

| Prompt | Formato | Modelo sugerido |
|---|---|---|
| ROTEADOR | 1 palavra (`vendas` \| `sac` \| `ignorar`), texto puro, sem JSON/tools | leve (GPT-4.1 nano ou equivalente), temperatura 0 |
| REVALIDADOR | 1 palavra (`humano` \| `bot`), texto puro, sem JSON/tools | leve, temperatura 0 |
| AGENTE(S) | JSON canônico NexTags, AVISOS ATIVOS, DADOS DESTA CONVERSA, transferência completa | {modelo do projeto} |

### 4.5 Como criar por API

```
GET  /accounts/custom_fields                 # listar antes (idempotente)
POST /accounts/custom_fields {"name":"motivo_transferencia","type":0}
POST /accounts/tags          {"name":"transacional"}
GET  /accounts/tags/name/{tag_name}          # conferir tag por nome
GET  /accounts/flows                         # validar TODO flow_id antes de usar
Base: https://app.nextagsai.com.br/api/   ·  header: X-ACCESS-TOKEN: <NEXTAGS_ACCESS_TOKEN>
Tipos: 0 Text · 1 Number · 2 Date · 3 DateTime · 4 Boolean · 5 Long Text · 6 Select · 7 Multi Select
```

---

## 5. Bateria de testes (4 a 6 casos-chave)

> Entregável de valor, não trava o processo: se não der para montar todos, entregue
> os que conseguir. Bateria completa de segurança em
> `assets/stress_test_battery_template.md`.

### Teste 1 — Abertura sem nome válido
**Cliente:** "oi" (com `{{first_name}}` = "Guest" / vazio)
**Esperado:** saudação neutra + pergunta do nome UMA vez; ao responder, grava
`set_field_value first_name`. Nunca "Oi, Guest!".

### Teste 2 — {Pergunta central do negócio}
**Cliente:** "{pergunta}"
**Esperado:** {resposta esperada, com a tool que deve ser chamada}

### Teste 3 — Fora de escopo
**Cliente:** "{pergunta fora do nicho}"
**Esperado:** redireciona com leveza mantendo a persona; na 2ª insistência, transfere.

### Teste 4 — Transferência para humano
**Cliente:** "{gatilho, ex.: 'meu pedido não chegou e já faz 15 dias'}"
**Esperado:** JSON com `motivo_transferencia` = `rastreio`, `prioridade_pipeline` =
`{media|alta}`, `resumo_pipeline` com contexto real, `send_flow`
`<ID_DO_FLUXO_PIPELINE>` por último. **Silêncio depois.**

### Teste 5 — Dado que não existe
**Cliente:** "{pergunta cuja tool retorna vazio}"
**Esperado:** não inventa; pede o dado correto ou escala. Nunca promete acompanhar.

### Teste 6 — Aviso ativo
**Setup:** preencher o bloco AVISOS ATIVOS com um feriado.
**Esperado:** o agente considera o aviso ao falar de prazo; com o bloco vazio, ignora.

---

## 6. Próximos passos

1. Preencher os placeholders da seção 2 e revalidar os `flow_id` em `GET /accounts/flows`.
2. Criar CUFs, tags e fluxos da seção 4 (dry-run antes: a API não apaga campo).
3. Rodar a bateria de testes num contato de teste real (WhatsApp; número fixo não
   recebe `send_flow` via API).
4. Ao editar o prompt depois, rodar a skill `nextags-prompt-fixer` — ela é idempotente.

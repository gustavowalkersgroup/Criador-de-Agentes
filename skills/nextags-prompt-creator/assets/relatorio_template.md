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
| `tipo_setor` | Seleção única (6): `humano`, `bot` — **criar na tela** | revalidador | {sim se 2+ IAs} |
| `motivo_transferencia` | Texto (0) | a IA | sim |
| `prioridade_pipeline` | Seleção única (6): `baixa`, `media`, `alta` — **criar na tela** | a IA | sim |
| `resumo_pipeline` | Texto (0) | a IA | sim |
| `resposta_ia` | Texto (0) | fluxo (Filtro JSON) | {sim se 2+ IAs} |
| `data_inicial_pipeline` | Data e hora (3) | fluxo de pipeline | sim |
| `data_vencimento` | Data e hora (3) | fluxo de pipeline (SLA) | sim |
| `horario_atendimento` | Texto (0) | fluxo | sim |
| `ultimo_atendimento` | Texto (0) | fluxo | recomendado |
| `nota_nps`, `comentario_nps`, `sugestao`, `data_nps` | Número (1) / Texto (0) / Texto (0) / Data e hora (3) | fluxo de NPS | {se houver NPS} |
| Transacionais (`numero_pedido`, `status_pedido`, `rastreio_url`, …) | todos Texto (0) | n8n | {se houver integração} |

⚠️ A API só cria CUF dos tipos **0 a 4** (texto, número, data, data e hora, sim/não). Os
tipos 5 (texto longo), 6 (seleção única) e 7 (seleção múltipla) são criados **na tela**
(Fluxos › aba Campo Personalizados); o tipo não muda depois de criado. Um valor `Data`/`Data e hora` vai em Unix timestamp em **segundos** e `sim/não` em
`1`/`0` (fonte: docs.nextags.com.br › Campos personalizados, campos do bot e variáveis).

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

Use o nome do modelo **exatamente como aparece** em Modelo (provedor), nos ajustes do
agente: a lista vem do provedor e muda quando ele lança ou aposenta um modelo. A
temperatura vai de 0 a 2 (o agente novo vem com 0,4).

### 4.5 Como criar por API

```
GET  /accounts/custom_fields                 # listar antes (idempotente)
POST /accounts/custom_fields {"name":"motivo_transferencia","type":0}
POST /accounts/tags          {"name":"transacional"}
GET  /accounts/tags/name/{tag_name}          # conferir tag por nome
GET  /accounts/flows                         # validar TODO flow_id antes de usar
Base: https://app.nextagsai.com.br/api/   ·  header: X-ACCESS-TOKEN: <NEXTAGS_ACCESS_TOKEN>
Tipos: 0 Text · 1 Number · 2 Date · 3 DateTime · 4 Boolean · 5 Long Text · 6 Select · 7 Multi Select
(a API cria só 0–4; 5, 6 e 7 só na tela. Bot field: o mesmo POST com "isBotField": true e "value".)
Limite: ~100 chamadas por minuto por conta, somando todas as integrações. Em lote, 1 por segundo.
```

---

## 5. Bateria de testes (4 a 6 casos-chave)

> Entregável de valor, não trava o processo: se não der para montar todos, entregue
> os que conseguir. Bateria completa de segurança em
> `assets/stress_test_battery_template.md`.

### Teste 1 — Abertura sem nome válido
**Cliente:** "oi" (com `{{first_name}}` = "Guest" / vazio)
**Esperado:** 1 mensagem só: saudação neutra + caminhos + pergunta com opções, sem
pedir o nome (OctoberCut). Se a pessoa disser o nome, grava `set_field_value first_name`.
Nunca "Oi, Guest!".

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

### Mensagens por cenário (OctoberCut)

Cada mensagem enviada é cobrada pela Meta desde 01/10/2026. Conte as bolhas de
cada resposta (itens de `messages` que não são typing).

| Cenário | Mensagens da empresa | Máximo esperado |
|---|---|---|
| Abertura | {n} | 1 |
| Diagnóstico / coleta de dados | {n} | 1 por rodada (máx. 1 rodada) |
| Vitrine (por produto) | {n} | 2 (imagem + botão) |
| Checkout / link de compra | {n} | 1 |
| Status de pedido | {n} | 1 |
| Handoff | {n} | 0–1 |

---

## 6. Subir o prompt e configurar o AI Hub

> O que o humano faz no painel (AI Hub › Agentes de IA › o agente) depois que o prompt
> está pronto. Fonte: help.nextags.com.br › Tutoriais › IA.

| # | Passo | Onde / como |
|---|---|---|
| 1 | Subir o prompt | Colar em **Mensagem do sistema (Prompt)** e **Salvar**, ou usar a skill `nextags-prompt-push` (`POST /agents/{id}` só com `{"prompt": ...}`; guarda backup do anterior e confere que o modelo não mudou). **Não** enviar `model` nem `max_output_tokens` pela API sem o usuário pedir (incidente de 23/10/2026): modelo e tokens o usuário ajusta no painel. |
| 2 | Ajustes do agente | Ícone de ajustes à direita de Mensagem do sistema: **Modelo** de cada provedor conectado (nome exato da lista), **Temperatura** 0–2 (vem 0,4), **Max tokens** 1–32768 (vem 2048; resposta cortada = aumentar), **Reasoning effort** e **Verbosity** (só aparecem em alguns modelos). Valores deste projeto: {modelo / temperatura / Max tokens}. Mude uma coisa por vez. |
| 3 | Tipo de resposta da IA | Este método faz o agente emitir o JSON NexTags pelo próprio prompt. No **Testar Agora**, confira que chegam bolhas, botões e imagens, e não texto com chaves e aspas. {Marcar Imagem/Vídeo/Áudio/Arquivo, Texto + Botões ou Carrossel só se o usuário decidir; imagens, vídeos e arquivos só saem com o link no prompt.} |
| 4 | Ferramentas de IA | Marcar no agente e **Salvar**: Servidores MCP (**Allowed tools**; a aba só existe com OpenAI, Gemini, Claude ou xAI conectado), Funções de IA, Arquivos (base de conhecimento; só com OpenAI; até 25 MB cada), Web Search. {Listar o que este projeto usa.} Diga no prompt quando consultar cada uma. |
| 5 | Ações de IA | Vazio por padrão: o handoff deste método é `send_flow` pelo JSON, com o trio canônico. Só criar regras de Ações de IA se o usuário decidir mover etiqueta/transferência para o painel. {Decisão: sim / não.} |
| 6 | Agente padrão | **Definir como agente padrão** (um por vez) e **Resposta Automática por IA** ligada em Configurações › Integrações › provedor. O agente padrão responde **antes** do fluxo de fallback. Sem os dois, o agente não responde sozinho. |
| 7 | Testar | **Testar Agora** (só aparece no agente padrão): perguntas comuns, fora de escopo, pedido de humano, dado que não existe. Antes de mudança grande, **Duplicar** o agente: a cópia é o backup. |
| 8 | Respostas que não vêm da IA | Conferir **Palavras-chave** e o fluxo de fallback: resposta sempre igual pode vir deles, não do agente. |
| 9 | Janela de 24 h | Mensagem livre só sai até 24 h após a última do contato (WhatsApp, Instagram, Messenger; TikTok 2 dias). Follow-up, transacional e disparo fora da janela exigem Modelo aprovado, num fluxo que comece com ele. |
| 10 | Contexto que a IA não viu | Pagamento, resposta por outro canal: `POST /contacts/{id}/ai/save_messages` com `role: developer` entra no histórico sem enviar nada ao contato. Na ação de IA do fluxo, **Lembrar conversa** = Sim. |

---

## 7. Próximos passos

1. Preencher os placeholders da seção 2 e revalidar os `flow_id` em `GET /accounts/flows`.
2. Criar CUFs, tags e fluxos da seção 4 (dry-run antes: a API não apaga campo; CUF tipo 6 se cria na tela).
3. Subir o prompt e ajustar o AI Hub (seção 6).
4. Rodar a bateria de testes num contato de teste real (WhatsApp; número fixo não
   recebe `send_flow` via API).
5. Ao editar o prompt depois, rodar a skill `nextags-prompt-fixer` — ela é idempotente.

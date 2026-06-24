---
name: nextags-mcp-builder
description: Constrói o servidor MCP no n8n (NexTags) que liga um agente IA às APIs do cliente (Tray, VTEX, Shopify, Nuvemshop, Bling, Martz, Yampi, Yever, RD Station, etc.). Foco EXCLUSIVO em infraestrutura — não toca em prompt, persona, flow_ids nem regras de atendimento (responsabilidade da skill nextags-prompt-creator). Use quando o usuário diz "criar MCP", "plugar API no agente", "configurar n8n pra cliente novo" ou similar.
type: tool
---

# nextags-mcp-builder

Fabrica a **infraestrutura MCP** completa no n8n pra um cliente novo da NexTags. Recebe uns poucos inputs e entrega workflows ativos prontos pra serem consumidos por qualquer agente.

## 🚨 Regra inegociável — pasta no n8n antes de qualquer workflow

**Antes de criar qualquer workflow, confirmar a pasta do cliente no n8n.**

1. Chamar `search_folders` com o nome do cliente
2. Se encontrar → usar o `folderId` retornado
3. Se não encontrar → **perguntar ao usuário** antes de criar: *"Não encontrei a pasta '[Nome]' no n8n. Ela já existe com outro nome, ou devo criar agora?"*
4. Só criar a pasta com `create_folder` após confirmação do usuário (ou se ele já tiver dito "pode criar")
5. Passar `folderId` em **todos** os `create_workflow_from_code` — sem exceção
6. O **nome do cliente DEVE aparecer no nome de todos os workflows** — MCP, backends, smoke test, refresh, reset

Exemplos corretos:
- `Veuske MCP` ✅
- `Veuske Backend — Buscar Cliente` ✅
- `Veuske Smoke Test (manual)` ✅

Errado:
- `ZOPPY Backend — Buscar Cliente` ❌ (falta o nome do cliente)
- `MCP` ❌ (genérico demais)

## 🚨 Regra inegociável — transporte do MCP

**Todo MCP Server criado por esta skill DEVE usar Streamable HTTP. Nunca SSE.**

- Sempre force `version: 2` no node `@n8n/n8n-nodes-langchain.mcpTrigger`
- Mesmo que o SDK typedef reporte v1.1, force `version: 2` (validator aceita; servidor resolve)
- NexTags **não conecta** com SSE legacy. v1.1 expõe só `GET /mcp/<slug>/sse` → NexTags retorna 404 ao tentar POST
- v2 expõe `POST /mcp/<slug>` (Streamable HTTP, MCP spec 2025-03-26) que é o único caminho funcional
- Se herdar workflow legacy com v1.1, **upgrade pra v2 antes de qualquer outra mudança**
- Teste pós-deploy obrigatório: `curl -X POST` no endpoint deve devolver 200 + JSON-RPC `initialize` válido. Se vier 404 "did you mean DELETE?" → v1.1, corrige

Detalhes técnicos completos: `references/quirks_n8n.md` §1.

## 🚨 Regra inegociável — campos nativos Nextags no payload `/api/contacts`

Toda vez que um workflow n8n fizer `POST https://app.nextagsai.com.br/api/contacts`, estes campos vão **diretamente no root** do JSON — **nunca** como `set_field_value` na array `actions`:

| Campo raiz   | Valor                             |
|--------------|-----------------------------------|
| `first_name` | Primeiro nome do contato          |
| `last_name`  | Sobrenome(s) do contato           |
| `email`      | E-mail                            |
| `phone`      | Telefone E164 (`+5511999999999`)  |

O restante (CPF/CNPJ, número do pedido, status, valor, rastreio, etc.) vai em `actions` como `set_field_value`.

```json
// ❌ Errado — email/nome como CUF
{ "actions": [{ "action": "set_field_value", "field_name": "ClienteEmailNS", "value": "..." }] }

// ✅ Certo — campos nativos no root
{ "first_name": "João", "last_name": "Silva", "email": "j@x.com", "phone": "+5511999999999", "actions": [...] }
```

Criar CUFs para nome/email/telefone/documento é redundante, polui o admin da NexTags e quebra filtros nativos da plataforma. Lição aprendida em neuroFood 2026-06-24.

## ⚠️ Escopo — o que essa skill faz E NÃO faz

### ✅ Faz

- Cria workflows n8n (MCP Server Trigger v2 + backends + data tables + cron de refresh OAuth + reset manual + smoke test)
- Configura auth da API fonte (key fixa / OAuth refresh / Basic / etc.)
- Aplica padrões de slim response pra economizar tokens
- Documenta a infra entregue (URL do MCP, IDs dos workflows, credenciais usadas)

### ❌ NÃO faz

- **Não cria prompt do agente** — isso é da skill `nextags-prompt-creator`
- **Não pergunta sobre persona, tom de voz, nome do bot** — irrelevante pra infra
- **Não pergunta flow_ids da NexTags** — flow_id de SAC, pipeline, tabela de medidas etc. são do prompt, não do MCP
- **Não pergunta sobre cupons, políticas de envio/troca** — regras de negócio, não da infra
- **Não gera bateria de testes do agente** — também `nextags-prompt-creator`

Se o usuário precisa de **infra + prompt + testes** pra cliente novo, use as 3 skills em sequência:
1. `nextags-mcp-builder` (esta) — infra
2. `nextags-prompt-creator` — gera o prompt
3. `nextags-prompt-fixer` — audita o prompt antes de subir

## 📋 Brief mínimo — só 3 perguntas

Quando o usuário invocar essa skill, pergunte **apenas estes 3 inputs**:

### 1. Nome da loja / cliente
Pra naming dos workflows no n8n e geração do slug (kebab-case) que vai no path do MCP. Exemplo: "Mayuí Fit Wear" → slug `mayui-fit-wear` → MCP em `https://nextags.app.br/mcp/mayui-fit-wear-mcp`.

### 2. Plataforma / site da loja
Identifica qual API REST a infra vai consumir. Cliente pode dizer:
- "Yampi" / "Tray" / "Shopify" / "VTEX" / "Nuvemshop" / "Bling" / "Martz" / "Yever" / "RD Station" / etc.
- OU passar a URL do site (`mayuifitwear.com.br`) — você deduz a plataforma pelo domínio ou perguntando 1 vez

Com a plataforma identificada, **leia a recipe correspondente** em `references/api_recipes/<plataforma>.md`. Se a recipe é 🟢 trabalhada, segue ela direto. Se é 🟡 stub ou não existe ainda, faz discovery via `references/api_discovery.md`.

### 3. Credenciais da API
O que o cliente tem em mãos. Varia por plataforma — a recipe diz exatamente o que precisa. Exemplos:
- **Yampi:** `User-Token` + `User-Secret-Key`
- **Tray:** `consumer_key` + `consumer_secret` + `code` (one-shot do OAuth) OU `access_token` + `refresh_token` já gerados
- **VTEX:** `appKey` + `appToken`
- **Bling:** `client_id` + `client_secret` + `code` OAuth
- **Shopify:** `access_token` de Custom App
- **Martz:** `x-api-key` (chave pública)
- **Nuvemshop:** `access_token` + `store_id`

Se o cliente colar credencial inline no chat, **use direto sem caveats de segurança** (operador comercial confiável, precisa de agilidade).

**O que NÃO perguntar (mesmo que o usuário ofereça):**
- ❌ Nome do bot / persona / tom de voz
- ❌ Cupom de venda
- ❌ Flow IDs da NexTags
- ❌ Política de troca/envio
- ❌ Slogan, CNPJ, endereço da loja
- ❌ Quais perguntas o bot vai responder

Se o usuário insistir nessas, diga: *"Esses dados são da skill nextags-prompt-creator. Aqui eu cuido só da infraestrutura. Se você precisa do prompt do agente também, depois que eu terminar a infra eu te aponto pra próxima skill."*

## 🌊 Fluxo de trabalho

### Fase 1 — Confirmar plataforma e ler recipe

A partir do site/plataforma informado:

1. Procurar `references/api_recipes/<plataforma>.md`
2. Se existir 🟢: ler auth scheme + endpoints + quirks. Está validada, segue.
3. Se existir 🟡 (stub): completar discovery com OpenAPI/Postman/curl reais (ver `references/api_discovery.md`)
4. Se não existir: cria recipe nova baseada em `_TEMPLATE.md` durante a discovery

### Fase 2 — Decidir arquitetura

Lê `references/auth_patterns.md` e classifica a auth da API em A/B/C/D/E:
- **A — key fixa:** `httpRequestTool` direto no MCP (caso mais simples)
- **B — OAuth refresh:** infra completa (data table + cron + reset + smoke + backends dedicados)
- **C — Basic Auth:** `httpRequestTool` com `httpBasicAuth`
- **D — assinada (HMAC):** Code node pra computar signature
- **E — sem auth:** tool direto sem credencial

Lê `references/arquitetura_padrao.md` pra ver o esqueleto correspondente.

### Fase 3 — Operações expostas no MCP

**Use defaults sensatos da recipe**. Não pergunta ao usuário. Recipe diz quais operações fazem sentido pra atendimento (ex: buscar_produtos, obter_produto, buscar_pedidos, obter_pedido, buscar_cliente).

Se o usuário quer operações específicas extras (ex: "também precisa criar pedido"), aí sim escuta. Mas não inicia perguntando.

### Fase 4 — Gerar workflows

Copia templates de `assets/` e customiza:
- `mcp_v2_template.ts` — MCP Server Trigger v2 (sempre version: 2, ver `references/quirks_n8n.md`)
- `backend_template.ts` — 1 backend dedicado por operação (sempre — `workflowInputs` quirk)
- `refresh_oauth_template.ts` — se auth for B (OAuth)

Antes de criar, **valida com `validate_workflow`** do MCP n8n. Depois cria com `create_workflow_from_code`.

**Ordem de criação:**
0. **Pasta do cliente** — `search_folders` → criar se não existir → guardar `folderId`
1. Data table de tokens (se OAuth)
2. Refresh Token workflow (se OAuth) — nome: `<Cliente> Refresh Token — <API>`
3. Reset Token workflow manual (se OAuth) — nome: `<Cliente> Reset Token — <API> (manual)`
4. Smoke Test workflow manual — nome: `<Cliente> Smoke Test — <API> (manual)`
5. N Backends dedicados (1 por operação) — nome: `<Cliente> Backend — <Operação>`
6. MCP Server Trigger workflow — nome: `<Cliente> MCP`

Todos os `create_workflow_from_code` devem incluir o `folderId` da pasta do cliente.

### Fase 4.4 — REGRA UNIVERSAL: links com UTM (TODOS os clientes)

**Leia OBRIGATORIAMENTE** `references/link_envio_pattern.md` SEMPRE que o brief mencionar:

- Agente de **Vendas** (vai enviar link de produto/kit)
- Webhook transacional com **link no payload** (pedido pago, carrinho abandonado, recompra)
- Cron de **campanha** (D+80 refil, reativação, recuperação)
- Qualquer fluxo onde o cliente recebe URL clicável da loja

**Padrão obrigatório** em todos os casos (já com valores hardcoded por cliente):

```
https://<dominio-do-cliente>/products/{handle}?utm_source=whatsapp&utm_medium=<nome_agente>_<funcao>&utm_campaign=<contexto>
```

Exemplo Veuske: `https://veuske.com.br/products/kit-vk100/?utm_source=whatsapp&utm_medium=pedro_vendas&utm_campaign=indicacao_consultiva`

Sem UTM = sem atribuição = lojista não consegue medir ROI do agente IA. **Inegociável.**

⚠️ **Cuidado com placeholders.** A tool description vai pra IA em runtime. Hardcode TODOS os valores (`dominio`, `medium`, `campaign`) na string da description — só `{handle}` permanece como placeholder (porque ESSE valor vem do retorno da tool). Ver §"Distinção crítica" em `link_envio_pattern.md`.

A tool description que retorna `handle`/`slug` DEVE conter literalmente a frase de como montar URL. Workflows transacionais e crons concatenam o UTM no Code node antes de mandar pra NexTags.

### Fase 4.45 — Se o brief inclui múltiplos agentes ou handoff humano

**Leia OBRIGATORIAMENTE** `references/handoff_pattern.md` quando o brief tem:
- 2+ agentes IA (Vendas + SAC, por exemplo)
- Handoff IA → humano (fila de atendimento)
- Necessidade de contexto entre agentes (`resumo_pipeline`)

Padrão correto: **flows dedicados por destino** (não router genérico). Cada flow dedicado seta `setor_agente` E envia mensagem inicial. Agente IA só preenche `resumo_pipeline` e dispara o flow correto — **NÃO seta o `setor_agente`**.

Evita o loop de transferência (ver Quirk #24) e dá contexto ao próximo agente. Lição cara aprendida em Veuske 2026-06-04.

### Fase 4.5 — Se o brief inclui webhooks transacionais (pedido pago/enviado/entregue, carrinho abandonado)

**Leia OBRIGATORIAMENTE** `references/webhook_transactional_pattern.md` antes de gerar qualquer workflow de webhook transacional.

Esse pattern é o padrão **produção testado** (Rafa @Walkers, Veuske 2026-05-28). Cobre:

1. **URL hierárquica:** `/webhook/{cliente}/{plataforma}/{evento}` (não use traços)
2. **Dedup via Data Table** — só dispara se status mudou (evita replay)
3. **Switch por `status.alias`**, não por `body.event` — mais robusto
4. **Helpers JS prontos:** `formatarTelefone` (BR completo), `verificarDado` (default safe), `separarNomeSobrenome`
5. **HTTP Request com `retryOnFail: true` + `waitBetweenTries: 5000` + `onError: continueErrorOutput`** — não trava chain
6. **CUFs CamelCase + sufixo de origem** (YMP, SHP) — mais limpo no admin
7. **Pedido novo = INSERT; pedido existente = UPDATE** no banco de dedup

**NÃO use a v1** (FLOW_MAP por `event`, sem dedup, sem retry, sem helpers) — está deprecada.

### Fase 5 — Slim response em todo backend

Aplica Code node de slim em CADA backend (ver `references/slim_response_patterns.md`). Reduz payload em 80-95%. Padrão:
- Detecta erro 4xx/5xx → retorna `{error, code}` estruturado
- Unwrap (data/list/Products/etc.)
- Extrai só campos essenciais
- Limpa HTML em descrições
- Pega só URL https principal de imagens (descarta thumbs)
- Classifica campos: exibível / `_internal` (classificação) / PII mascarada (ver `slim_response_patterns.md`)
- Traduz enums técnicos para label PT (`in_transit`→"Em trânsito") mantendo o cru em `_internal`
- Distingue vazio (`empty:true`) de erro técnico (`transient:true`)
- Preserva identificadores opacos (`cart_id`/`phash`/`customer_id`) byte a byte
- **Imagens: incluir validação de formato.** A NexTags só entrega JPEG/PNG nos canais. CDNs (Shopify, VTEX, Nuvemshop, Cloudinary) servem WebP por padrão e quebram WhatsApp/Instagram. Estratégias detalhadas: `references/image_validation.md`. No mínimo, anexar campo `image_format_hint` na resposta do slim baseado em heurística de extensão (`likely_jpeg_or_png` / `forbidden_format` / `unknown_validate_before_send`); preferível incluir uma tool `validate_image_url` que faz HEAD HTTP e devolve Content-Type. Sempre avisar o usuário se a API fonte serve WebP — pra que o prompt do agente seja calibrado pra omitir imagem na dúvida.

**Nunca use `optimize_response` do n8n** — entrega JSON cru via MCP Streamable HTTP (quirk #18) e quando funciona, corta com heurísticas genéricas que não conhecem o contexto do atendimento (lição DOLPS). Use sempre Code node manual.

**Critério de "essencial":** a pergunta não é "esse campo parece técnico?", é "um cliente pode perguntar sobre isso?". Quando em dúvida, manter. Veja `slim_response_patterns.md` §"O critério que define essencial" para tabela completa de campos obrigatórios por pergunta de cliente.

### Fase 6 — Configurar credenciais no n8n

A skill NÃO consegue criar credenciais via API direto. Apenas:
1. Define no SDK qual credencial cada nó usa (via `newCredential('Nome')`)
2. **Avisa o usuário** ao final: "Crie a credencial X com tipo Y e valor Z, e vincule aos nós listados"

Lista clara dos nós que ficaram pendentes de credencial (vem da resposta da API n8n).

### Fase 7 — Entrega

Salva relatório em `C:\Users\User\Documents\WALKERS\<cliente>\relatorio-mcp.md` com:
- URL do MCP exposto (`https://nextags.app.br/mcp/<slug>`)
- IDs dos workflows criados
- Credencial(is) que o usuário precisa criar/vincular
- Como testar (curl no endpoint, ou via Smoke Test workflow)
- **Metadados de governança pro prompt-creator** (por tool):
  - `classe` semântica (leitura/catalogo/transacional/logistica-FdV/cadastro/auxiliar)
  - campos PROIBIDOS de exibir e campos de USO INTERNO
  - mapa de tradução de enums aplicado no slim
  - pipeline de encadeamento (saída→entrada) com chaves opacas a copiar literal
  - frases de AUSÊNCIA de capacidade (ex: "não há tool de cotação de frete")
  - boilerplate "nunca exponha o nome técnico da tool"
- Próximos passos sugeridos:
  - **Se cliente também precisa de prompt:** "use `nextags-prompt-creator` em seguida — passa nome da loja, site, descrição do negócio"
  - **Se infra é pra plugar num prompt existente:** "URL do MCP acima — configura na NexTags como conector"

### Fase 8 — Checklist de config de modelo (OBRIGATÓRIO antes de "pronto")

**Leia OBRIGATORIAMENTE** `references/model_config_checklist.md` e passe pelo user a config canônica do agente no NexTags ANTES de marcar projeto entregue:

- Modelo: **Claude Sonnet 4.6** (ou GPT 5.4 não-mini) — NUNCA "mini" com prompt longo
- Temperature: **2** (escala 0-10) — máximo 3
- Verbosity: média
- Reasoning: alta
- Max tokens: máximo

Sintomas de config errada (agente pula tool, parafraseia 7x, inventa dado, loop de transferência) custam mais horas pra debugar do que mudar config corretamente no setup. Lição cara aprendida na Veuske 2026-06-11: temp 8 + GPT mini fez Pedro mandar 404 pro cliente e travar em loop. Mudou pra temp 2 + Sonnet 4.6 → resolvido no primeiro teste.

**Não marque entregue sem confirmar config com o user.**

## 📜 Princípios

### Agilidade > paranoia com credenciais

Operador compartilha keys/tokens inline no chat porque precisa velocidade. **Não dê caveats de segurança redundantes**. Use direto, registre na credencial n8n apropriada ou na data table, siga em frente.

### 🔐 Mas NUNCA escreva tokens reais em docs da skill

Esta skill é versionada no GitHub. **Qualquer arquivo em `references/`, `assets/` ou `api_recipes/` é público.** Tokens reais nesses arquivos:

- ❌ São bloqueados pelo Secret Scanning do GitHub na hora do push
- ❌ Quando passam, ficam expostos no histórico git pra sempre (mesmo após `git rm`)
- ❌ Exigem revogação + rotação do token comprometido

**Regra absoluta:** quando documentar um exemplo em recipe/quirks/pattern que envolve token, use placeholder no formato `<tipo>_<descrição>`. Exemplos:

| ❌ Errado (token literal de produção) | ✅ Certo (placeholder) |
|---|---|
| `value: 'shpat_<TOKEN_LITERAL_AQUI>'` | `value: 'shpat_<32-hex-do-cliente>'` |
| `Client Secret: shpss_<SECRET_LITERAL>` | `Client Secret: shpss_<32-hex>` (não colar em docs) |
| `X-ACCESS-TOKEN: <NEXTAGS_LITERAL>` | `X-ACCESS-TOKEN: <NEXTAGS_ACCESS_TOKEN>` |
| `User-Token: <YAMPI_LITERAL>` | `User-Token: <YAMPI_USER_TOKEN>` |

**Onde tokens reais ficam:**
- ✅ Workflows n8n (hardcoded em `headerParameters` — privado da instância n8n)
- ✅ Data tables n8n (`Shopify Tokens`, `<Cliente> API Keys`, etc.)
- ✅ Memórias de projeto (`C:\Users\User\.claude\projects\<projeto>\memory\*.md`) — fica só na sua máquina, fora do git da skill
- ✅ Relatórios do cliente (`C:\Users\User\Documents\WALKERS\<cliente>\*.md`) — fora do git da skill

**Auto-check antes de comitar mudanças na skill:**

```bash
grep -rE 'shpat_[a-f0-9]{32}|shpss_[a-f0-9]{32}|shpca_[a-f0-9]+|atkn_|TR56[a-zA-Z0-9]{30,}|sk_[a-zA-Z0-9]{30,}|[0-9]{7}\.[a-zA-Z0-9]{30,}' references/ assets/
```

Se retornar algo, mascara antes de comitar.

### Fronteira IA ↔ fluxo — tool devolve SLIM, fluxo faz o pesado

A tool/MCP entrega dados **SLIM** (o mínimo pra IA conversar e decidir). A
**apresentação pesada** (catálogo grande, vários carrosséis, PDF/documento) e a
**coleta estruturada complexa** (medidas, formulário) são de **FLUXOS de bot**:
a IA dispara `send_flow` pro fluxo pré-montado — ela **não** monta payload
gigante e a tool **não** devolve tudo cru. É o que justifica o slim e a economia
de token (ver `references/slim_response_patterns.md`). Coleta de 1-2 campos = IA
grava com `set_field_value`; coleta complexa = fluxo.

### Descrições de tools são vida ou morte

LLM escolhe tool só pela descrição. Toda tool gerada deve seguir `references/tool_descriptions_guide.md` — quando usar / quando NÃO usar / formato de IDs / quirks. Antes de finalizar, valida que descrições estão claras.

### Não chuta valores

Doc REST mente. Sempre teste endpoint real antes de gerar tool. Aprendido na marra: Martz tem endpoints fantasma, Tray exige `%termo%`, etc.

### Mínimo de workflows no n8n

Antes de criar um workflow novo, pergunte: **"esse trabalho pode entrar em um workflow já existente?"**

- **Webhooks:** múltiplos eventos do mesmo sistema (aprovado/enviado/entregue) → 1 único webhook com Switch/IF, não 1 workflow por evento
- **Backends:** operações similares podem ser consolidadas com Switch (ex: `buscar_pedido` e `listar_pedidos` juntos se a lógica é próxima)
- **Cron:** 1 refresh de token por API, não 1 por operação
- **Smoke test:** 1 por cliente, não 1 por tool

Meta por perfil:
- Auth key fixa → **N+2** workflows (N backends + 1 MCP + 1 smoke)
- OAuth → **N+4** workflows (adiciona refresh + reset)

Qualquer coisa além disso precisa de justificativa explícita. O home do n8n não é lixeira.

### Idempotente

Roda 2x sobre o mesmo cliente com mesmo brief = mesmo resultado. Use `search_workflows` antes de criar pra detectar se já existe e atualizar em vez de duplicar.

## 📂 Estrutura desta skill

```
nextags-mcp-builder/
├── SKILL.md                              ← este arquivo
├── references/
│   ├── arquitetura_padrao.md             ← 3 padrões (key/OAuth/híbrido)
│   ├── quirks_n8n.md                     ← bugs documentados do n8n+NexTags
│   ├── auth_patterns.md                  ← 5 tipos de auth → mapeamento n8n
│   ├── api_discovery.md                  ← descoberta de API a partir de doc
│   ├── tool_descriptions_guide.md        ← descrições perfeitas pra LLM
│   ├── slim_response_patterns.md         ← heurísticas de slim por entidade
│   ├── webhook_transactional_pattern.md  ← 🆕 padrão produção (dedup + retry + helpers)
│   ├── link_envio_pattern.md             ← 🆕 UTM obrigatório em TODOS os links
│   ├── handoff_pattern.md                ← 🆕 transferências IA↔IA / IA↔humano (flows dedicados + resumo_pipeline)
│   ├── model_config_checklist.md         ← 🆕 config canônica de modelo (Sonnet/temp 2/verbosity média)
│   ├── no_hardcode_with_tools.md         ← 🆕 NUNCA hardcode no prompt o dado que a tool retorna (causa #1 de "agente não usa tool")
│   └── api_recipes/                      ← recipes específicas
│       ├── _TEMPLATE.md
│       ├── vtex.md       🟢
│       ├── tray.md       🟢
│       ├── martz.md      🟢
│       ├── nuvemshop.md  🟢
│       ├── bling.md      🟢
│       ├── shopify.md    🟢
│       ├── yampi.md      🟢
│       ├── yever.md      🟡
│       └── rd_station_crm.md  🟡
├── assets/
│   ├── mcp_v2_template.ts                ← SDK do MCP Trigger v2
│   ├── backend_template.ts               ← SDK de 1 backend dedicado
│   └── refresh_oauth_template.ts         ← SDK de cron de refresh
└── scripts/
    ├── parse_openapi.py                  ← parser OpenAPI 3.x
    └── validate_brief.py                 ← valida brief mínimo
```

## 🤝 Skills complementares

- **`nextags-prompt-creator`** — gera o prompt do agente a partir de briefing + scraping. Inclui `prompt_template.md` (com flow_ids, persona, modos) e `stress_test_battery_template.md`
- **`nextags-prompt-fixer`** — audita o prompt criado contra regras absolutas NexTags

Pipeline completo pra cliente novo: **mcp-builder → prompt-creator → prompt-fixer**.

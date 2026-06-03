# TroqueCommerce (trocas, devoluções e logística reversa)

> Status: 🟡 stub — **webhook outbound ✅ CONFIRMADO** (pronto pra produção); **API pull (MCP) a confirmar** via discovery na conta de um lojista.
> Última atualização: 2026-06-03
> Cliente(s) usando: —

**⚠️ Camada de integração (ponto-chave):** o que importa aqui é a API/webhook da **própria TroqueCommerce**, NÃO a da plataforma de e-commerce do lojista (Shopify/Nuvemshop/VTEX/Tray/etc.). A TroqueCommerce roda POR CIMA do e-commerce e já consome a API dele internamente; a NexTags se pluga na camada TroqueCommerce. Domínio correto: **`troquecommerce.com.br`** (portais de autoatendimento do cliente final ficam em `*.troque.app.br`, ex.: `dimyoficial.troque.app.br`). NÃO use `troc.com.br`.

## 🔗 Base URL e ambientes

- **Site/admin:** `https://www.troquecommerce.com.br`
- **Portal de troca do cliente final:** `https://<loja>.troque.app.br`
- **API REST pull (partner-facing):** 🟡 **base URL a confirmar** — não há portal dev público (`developers.troquecommerce.com.br` redireciona pra home). Fonte de discovery: coleção **Postman `magecore/troquecommerce`** (workspace id `1092259`). Rodar discovery com access token real (ver `references/api_discovery.md`).
- **Versão atual:** desconhecida (confirmar na discovery).
- **Variação por loja?** Não para a API TroqueCommerce; o subdomínio `*.troque.app.br` é só o portal do cliente final.

## 🔐 Autenticação

- **Tipo:** **A (chave fixa)** — access token gerado no admin do lojista. Sem indício de OAuth/refresh (sem cron, sem data table de token).
- **Como obter:** admin TroqueCommerce do lojista → **"Automações e Integrações"** (e/ou área de API) → gerar/copiar o token de acesso.
- **Uso no webhook (inbound TC→n8n):** token vai **no fim da URL** do receptor; **Header em branco** (sem HMAC/assinatura).
- **Uso no pull (n8n→TC):** token fixo no header da requisição (formato exato a confirmar na discovery).
- **Credencial n8n:** Pattern A — header fixo no node HTTP do backend.

## 📡 Webhook outbound (TroqueCommerce → n8n) — ✅ CONFIRMADO (espinha dorsal)

É o caminho mais robusto e **suficiente por si só**. Construa SEMPRE, seguindo `references/webhook_transactional_pattern.md` adaptado para a entidade **troca**.

### Configuração no admin TroqueCommerce
Menu **"Automações e Integrações" → "Webhook"**:
1. **Ativar** o toggle.
2. **Nome:** livre (ex.: `NexTags`).
3. **URL:** colar a URL do receptor n8n com o **token no fim**:
   `https://nextags.app.br/webhook/<slug-cliente>/troquecommerce/trocas/<TOKEN>`
   (padrão observado na integração E-Vendas: `.../troquecommerce/<TOKEN>`).
4. **Header:** **deixar EM BRANCO** — sem HMAC. A autenticidade vem do token embutido na URL (segredo de caminho); o receptor valida esse token no path antes de processar.
5. **Eventos:** marcar os do ciclo de troca (checkboxes).
6. **Salvar.**

### Eventos (🟡 nomes exatos só na conta do lojista — capturar 1 disparo real)
Ciclo esperado: **solicitada** → **aprovada** → **produto recebido** (reversa concluída) → **reembolso efetuado / vale-troca gerado** → **recusada/cancelada**.

### Receiver n8n (regras herdadas do padrão transacional)
- **Dedup** via Data Table por id da troca (`troca_id`, `status`, `updated_at`) — evita msg duplicada em replay (alta probabilidade no setor).
- **Switch por STATUS da troca**, não por event genérico. Troca nova = INSERT; existente = UPDATE; status igual ao anterior = ignora (replay).
- HTTP NexTags com `retryOnFail: true` + `waitBetweenTries: 5000` + `onError: continueErrorOutput`; token NexTags hardcoded no header.
- Helpers defensivos (`verificarDado`, `formatarTelefone`, `separarNomeSobrenome`) — payload pode vir incompleto.

## 📦 API REST pull (n8n → TroqueCommerce) — 🟡 PROVÁVEL, a confirmar

Para o agente **consultar** status sob demanda (em vez de só receber push). Evidências: o admin gera access token e há coleção Postman pública — indica REST. Lacuna: base URL e rotas partner-facing não documentadas.

**Endpoints esperados (validar via Postman/discovery):**

| Caso de uso | Endpoint esperado |
|---|---|
| Status de uma troca | `GET /exchanges/{id}` (ou `/trocas/{id}`) |
| Trocas de um pedido | `GET /exchanges?order_id={id}` |
| Criar solicitação (opcional) | `POST /exchanges` *(só se exposto)* |

**Fallback:** se NÃO houver API de consulta partner-facing → **webhook-only**: o agente lê os CUFs que o webhook já preencheu, sem perda funcional relevante pra atendimento.

## 🧰 Tools MCP sugeridas (se a discovery confirmar a API) — Pattern A

- `consultar_troca` — status de uma troca por id.
- `listar_trocas_do_pedido` — trocas de um pedido (por número/id do pedido).
- `criar_solicitacao_troca` — *opcional*, só se a API expuser POST.

Aplicar **slim response** em cada backend. Se a API servir imagem WebP, anexar `image_format_hint` (NexTags só entrega JPEG/PNG nos canais — ver `references/image_validation.md`).

## 🏷️ Mapeamento eventos → CUFs (CamelCase + sufixo `TRC`)

| CUF | Conteúdo |
|---|---|
| `StatusTrocaTRC` | Status atual (solicitada/aprovada/recebida/reembolsada…) |
| `CodigoTrocaTRC` | Identificador da solicitação de troca |
| `NumeroPedidoTRC` | Pedido de origem |
| `ProdutoTrocaTRC` | Produto(s) em troca |
| `MotivoTrocaTRC` | Motivo informado pelo cliente |
| `ValorValeTRC` | Valor de vale-troca/crédito/reembolso |
| `RastreioReversaTRC` | Código de rastreio da logística reversa |

> O `send_flow` (qual flow disparar por status) **NÃO** é definido na infra — é responsabilidade do prompt do agente (`nextags-prompt-creator`). A infra deixa o placeholder de `flow_id`.

## ⚠️ Quirks documentados

- **Webhook sem HMAC** — segurança é só o token no path; use token longo/aleatório, valide no path, rotacione se vazar.
- **Payload do webhook não documentado** — capturar 1 disparo real no n8n pra mapear estrutura e nomes de eventos antes de fixar o Switch.
- **Sem portal dev / sem specs públicas** — discovery obrigatória via Postman + token real.
- **Não confundir com a API do e-commerce** — integrar a camada TroqueCommerce, não Shopify/Nuvemshop/etc.

## 📋 Decisão de arquitetura recomendada

Duas camadas (ver `arquitetura_padrao.md` + `webhook_transactional_pattern.md`):
1. **Webhook receiver (sempre)** — backbone; empurra status de troca pros CUFs e dispara flows.
2. **MCP pull (Caso A, condicional à discovery)** — `consultar_troca` / `listar_trocas_do_pedido` como `httpRequestTool` direto no MCP, com slim response. Sem API → webhook-only.

## 🔗 Links

- Site oficial: https://www.troquecommerce.com.br/home
- Mecanismo do webhook (via integração E-Vendas): https://ajuda.troquecommerce.com.br/pt/article/como-integrar-o-e-vendas-com-a-troquecommerce-1c27n8f/ · https://www.e-vendas.net.br/como-integrar-com-a-troquecommerce/
- Coleção Postman (discovery de endpoints): https://www.postman.com/magecore/workspace/troquecommerce/collection/1092259-b813dca9-a685-4355-a432-5c0bcc00460b
- Central de ajuda: https://ajuda.troquecommerce.com.br/pt/
- Apps: Shopify https://apps.shopify.com/troquecommerce · VTEX https://apps.vtex.com/troquecommercepartnerbr-troquecommerce-io/p
- Confiabilidade: média (webhook verificado em doc de parceiro; API pull não confirmada).

## 📝 Notas históricas

- 2026-06-03: recipe criada a partir do estudo de viabilidade (webhook confirmado, MCP pull a confirmar). Domínio corrigido para `troquecommerce.com.br` (versões antigas usavam `troc.com.br`, errado). Promover para 🟢 após discovery numa conta de lojista ativa: payload real, lista de eventos e base URL/rotas da API pull.

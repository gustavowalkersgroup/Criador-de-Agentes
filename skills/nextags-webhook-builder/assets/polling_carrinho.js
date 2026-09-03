// ═══════════════════════════════════════════════════════════════
// TEMPLATE: CRON DE CARRINHO ABANDONADO (polling)
// Use quando a plataforma NÃO tem webhook nativo de carrinho:
//   Shopify (GET /checkouts), Nuvemshop (GET /checkouts), Tray, Magazord,
//   Conecta Venda. Ex.: Exclusiva cron, Nalisa, Alto Giro, Wazzu feeder.
// (Se a plataforma EMITE webhook de carrinho — Yampi, Martz — use um
//  webhook simples, NÃO este cron.)
// Sem credencial nativa da loja? Ver references/gateway_proxy_nextags.md.
//
// Polling SEMPRE precisa de dedup (senão redispara o mesmo carrinho a cada tick).
//
// WIRING (dedup grava SÓ no sucesso — regra nº2):
//   Schedule Trigger (a cada 30min)
//     → HTTP GET carrinhos abertos da plataforma  (ou Gateway Proxy NexTags)
//     → Split em itens
//     → Code "Normalizar + guards" (abaixo)
//     → Data Table: rowNotExists por checkout_id  (dedup gate)
//     → [opcional] checar conversão (o carrinho virou pedido? então pula)
//     → Notificar NexTags (onError: continueErrorOutput)
//     → IF "Notificação OK?"
//          ├─ true  → Salvar Estado (Data Table INSERT)   ← só aqui grava dedup
//          └─ false → Falhou (NoOp, NÃO grava)
//
// ⚠️ Foi exatamente aqui que o Carrinho v1 da Nordmann (bvR8NeB5e4BdOzyD)
//    queimou 51 clientes: 401 em todas as chamadas e dedup gravado do mesmo jeito.
// ═══════════════════════════════════════════════════════════════

// (cole os helpers de _helpers.js acima)
const FLOW_CARRINHO = 0;                  // <- 0 = fail-safe: NÃO dispara até colocar o flow_id REAL
const ORIGEM = '<shopify>';               // vai no CUF origem_pedido
const DOMINIO = '<dominio-do-cliente.com.br>';   // vazio bloqueia o disparo de propósito (link quebrado é pior)
const IDADE_MIN_H = 1;                    // só dispara carrinho com 1h..48h de idade
const IDADE_MAX_H = 48;

const cart = $input.first().json;
const customer = (cart.customer && cart.customer.data) || cart.customer || {};

const checkout_id = String(cart.id || cart.token || cart.checkout_id);   // chave de dedup
const base = { checkout_id };

// ---- guards -------------------------------------------------------
const g = guardTelefone((customer.phone && customer.phone.full_number) || customer.phone);
if (!g.ok) return skip(base, g.motivo);                 // sem_telefone | telefone_invalido | telefone_fixo
if (!FLOW_CARRINHO) return skip(base, 'flow_id_ausente:carrinho');

const criadoEm = new Date(cart.created_at || cart.updated_at || cart.abandoned_at);
const horas = (Date.now() - criadoEm.getTime()) / 3600000;
if (!(horas >= IDADE_MIN_H && horas <= IDADE_MAX_H)) return skip(base, 'fora_da_janela');

if (cart.order_id || cart.completed_at) return skip(base, 'ja_convertido');   // virou pedido

// link de checkout COM UTM (nunca sem, nunca colando '&' sem '?')
const linkBruto = verificarDado(
  (cart.spreadsheet && cart.spreadsheet.data && cart.spreadsheet.data.purchase_url) ||
  cart.abandoned_checkout_url || cart.checkout_url || `https://${DOMINIO}/checkout/${checkout_id}`, '');
if (!linkBruto) return skip(base, 'sem_link_carrinho');   // melhor não mandar nada do que link quebrado (Degan)

const itensArr = (cart.items && cart.items.data) || cart.items || cart.line_items || [];
const { nome, sobrenome } = separarNomeSobrenome(verificarDado(customer.name || customer.first_name, ''));

return [{ json: {
  ...base,
  flow_id: String(FLOW_CARRINHO),
  phone: g.phone,
  first_name: nome,
  last_name: sobrenome,
  email: verificarDado(customer.email, ''),
  // CUFs CANÔNICOS de carrinho (campos_canonicos.md §5)
  produtos_carrinho: itensArr
    .map(i => `${verificarDado(i.title || i.name)} (Qtd: ${verificarDado(i.quantity)})`)
    .join(', ') || 'itens do carrinho',
  qtd_itens_carrinho: String(itensArr.length || 0),
  valor_carrinho: valorTexto(cart.total || cart.total_price || cart.subtotal),
  link_carrinho: comUTM(linkBruto, 'cron_carrinho', 'carrinho_abandonado'),
  origem_pedido: ORIGEM,
}}];

// ---- Data Table dedup: <Cliente> <Plataforma> Carrinho Dedup --------
//   colunas: checkout_id (string) | notified_at (string)
//   Dedup gate: operação nativa rowNotExists por checkout_id (mais direto que get + IF
//   quando só importa a existência da linha — Alto Giro "Dedup Gate").
//   ⚠️ Antes de disparar, se a API permitir, confirme que o checkout NÃO virou pedido.
//
// ---- HTTP Request NexTags (specifyBody:'json', retryOnFail:true,
//      waitBetweenTries:5000, onError:continueErrorOutput) --------------
// jsonBody:
// {
//   "phone":"={{ $json.phone }}","first_name":"={{ $json.first_name }}",
//   "last_name":"={{ $json.last_name }}","email":"={{ $json.email }}",
//   "actions":[
//     {"action":"set_field_value","field_name":"produtos_carrinho","value":"={{ $json.produtos_carrinho }}"},
//     {"action":"set_field_value","field_name":"qtd_itens_carrinho","value":"={{ $json.qtd_itens_carrinho }}"},
//     {"action":"set_field_value","field_name":"valor_carrinho","value":"={{ $json.valor_carrinho }}"},
//     {"action":"set_field_value","field_name":"link_carrinho","value":"={{ $json.link_carrinho }}"},
//     {"action":"set_field_value","field_name":"origem_pedido","value":"={{ $json.origem_pedido }}"},
//     {"action":"add_tag","tag_name":"transacional"},
//     {"action":"send_flow","flow_id":"={{ $json.flow_id }}"}
//   ]
// }
// ⚠️ Ordem fixa: set_field_value… → add_tag… → send_flow por último.
// Header: X-ACCESS-TOKEN: <NEXTAGS_ACCESS_TOKEN>  (preferir credencial nomeada do n8n)
// Em polling grande, batchSize 1 + intervalo (~600ms): rate limit NexTags ~100 req/60s (Privilège).

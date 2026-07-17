// ═══════════════════════════════════════════════════════════════
// TEMPLATE: CRON DE CARRINHO ABANDONADO (polling)
// Use quando a plataforma NÃO tem webhook nativo de carrinho:
//   Shopify (GET /checkouts), Nuvemshop (GET /checkouts), Tray, Magazord,
//   Conecta Venda. Ex.: Exclusiva cron, Nalisa, Alto Giro, Wazzu feeder.
// (Se a plataforma EMITE webhook de carrinho — Yampi, Martz — use um
//  webhook simples, NÃO este cron.)
//
// Polling SEMPRE precisa de dedup (senão redispara o mesmo carrinho a cada tick).
//
// WIRING:
//   Schedule Trigger (a cada 30min)
//     → HTTP GET carrinhos abertos da plataforma
//     → Split em itens
//     → Code "Normalizar + guards" (abaixo)
//     → Data Table Get por checkout_id → IF novo? → segue / NoOp
//     → [opcional] checar conversão (o carrinho virou pedido? então pula)
//     → HTTP Request NexTags → Data Table INSERT (marca disparado)
// ═══════════════════════════════════════════════════════════════

// (cole os helpers de _helpers.js acima)
const FLOW_CARRINHO = '<FLOW_ID_CARRINHO_ABANDONADO>';
const DOMINIO = '<dominio-do-cliente.com.br>';
const IDADE_MIN_H = 1;    // só dispara carrinho com 1h..48h de idade
const IDADE_MAX_H = 48;

const cart = $input.first().json;
const customer = (cart.customer && cart.customer.data) || cart.customer || {};

const checkout_id = String(cart.id || cart.token || cart.checkout_id);   // chave de dedup
const phone = formatarTelefone((customer.phone && customer.phone.full_number) || customer.phone);

// guard de idade (evita disparar carrinho recém-criado ou velho demais)
const criadoEm = new Date(cart.created_at || cart.updated_at || cart.abandoned_at);
const horas = (Date.now() - criadoEm.getTime()) / 3600000;
const idadeOk = horas >= IDADE_MIN_H && horas <= IDADE_MAX_H;

const itens = ((cart.items && cart.items.data) || cart.items || cart.line_items || [])
  .map(i => `${verificarDado(i.title || i.name)} (Qtd: ${verificarDado(i.quantity)})`)
  .join(', ') || 'itens do carrinho';

// link de checkout COM UTM (nunca sem, nunca colando '&' sem '?')
const linkBruto = verificarDado(
  (cart.spreadsheet && cart.spreadsheet.data && cart.spreadsheet.data.purchase_url) ||
  cart.abandoned_checkout_url || cart.checkout_url || `https://${DOMINIO}/checkout/${checkout_id}`, '');
const link = comUTM(linkBruto, 'cron_carrinho', 'carrinho_abandonado');

const { nome, sobrenome } = separarNomeSobrenome(verificarDado(customer.name || customer.first_name, ''));

return [{ json: {
  checkout_id, phone, first_name: nome, last_name: sobrenome, itens, link,
  flow_id: FLOW_CARRINHO,
  _skip: !phone || !idadeOk,     // sem telefone ou fora da janela → não dispara
}}];

// ---- Data Table dedup: <Cliente> Carrinho Dedup --------------------
//   colunas: checkout_id (string) | notified_at (string)
//   IF: linha existe por checkout_id → NoOp (já avisado).  Senão dispara + INSERT.
//   ⚠️ Antes de disparar, se a API permitir, cheque se o checkout NÃO virou pedido (conversão).
//
// ---- HTTP Request NexTags (specifyBody:'json', retryOnFail, onError:continue) ----
// jsonBody:
// {
//   "phone":"={{ $json.phone }}","first_name":"={{ $json.first_name }}","last_name":"={{ $json.last_name }}",
//   "actions":[
//     {"action":"set_field_value","field_name":"StatusPedido","value":"Carrinho"},
//     {"action":"set_field_value","field_name":"ProdutosCarrinho","value":"={{ $json.itens }}"},
//     {"action":"set_field_value","field_name":"LinkCarrinho","value":"={{ $json.link }}"},
//     {"action":"send_flow","flow_id":"={{ $json.flow_id }}"}
//   ]
// }
// Header: X-ACCESS-TOKEN: <NEXTAGS_ACCESS_TOKEN>
// Em polling grande, use batchSize 1 + intervalo ~500ms p/ respeitar rate limit (anti-429).

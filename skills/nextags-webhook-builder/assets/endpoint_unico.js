// ═══════════════════════════════════════════════════════════════
// TEMPLATE: ENDPOINT ÚNICO + SWITCH POR STATUS
// Use quando a plataforma manda 1 evento genérico com status variável
// (Bling pedido_venda.alterado, VTEX, Tray order_changed).
// Ex. produção: Veuske (Yampi), Amo Calçados (Bling), Dolps (VTEX), BB (Tray).
//
// WIRING no n8n:
//   Webhook (POST /webhook/{cliente}/{plataforma}/pedidos)
//     → [se HMAC] Code valida assinatura → responde 200
//     → Code "Normalizar" (este arquivo, bloco A)
//     → Data Table: Get row por order_id  (dedup lookup)
//     → IF "status mudou?" (bloco B)
//         └ TRUE → Switch por status → HTTP Request NexTags → Data Table upsert
//         └ FALSE → NoOp (dedup: já disparado)
//   HTTP Request: retryOnFail:true, waitBetweenTries:5000,
//                 onError:continueErrorOutput, specifyBody:'json'
// ═══════════════════════════════════════════════════════════════

// ---- BLOCO A: normalizar (Code node) --------------------------------
// (cole os helpers de _helpers.js acima)
const body = $input.first().json.body || $input.first().json;
const order = body.resource || body.data || body;                 // ajuste ao payload da plataforma
const customer = (order.customer && order.customer.data) || order.customer || {};

// Switch por status.alias (NUNCA por body.event) — mais robusto
const statusAlias = verificarDado(
  (order.status && order.status.data && order.status.data.alias) || order.status_alias || order.situacao,
  'desconhecido'
);

const order_id = String(order.id || order.order_id);              // INTERNO → chave de dedup
const order_number = String(order.number || order.order_number || order.id); // EXIBIÇÃO → CUF
const { nome, sobrenome } = separarNomeSobrenome(
  verificarDado((customer.first_name ? customer.first_name + ' ' + (customer.last_name||'') : customer.name), '')
);
const itens = ((order.items && order.items.data) || order.items || [])
  .map(i => `${verificarDado((i.sku && i.sku.data && i.sku.data.title) || i.title)} (Qtd: ${verificarDado(i.quantity)}, R$ ${verificarDado(i.price || i.item_value)})`)
  .join(', ') || 'Nenhum item';

// flow_id por status — PREENCHER com os flow_ids REAIS do NexTags (nunca placeholder!)
const FLOW_BY_STATUS = {
  paid:      '<FLOW_ID_APROVADO>',
  shipped:   '<FLOW_ID_ENVIADO>',
  delivered: '<FLOW_ID_ENTREGUE>',
  // cancelled: '<FLOW_ID_CANCELADO>',
};
const flow_id = FLOW_BY_STATUS[statusAlias];

return [{ json: {
  order_id, order_number, statusAlias, flow_id,
  phone: formatarTelefone((customer.phone && customer.phone.full_number) || customer.phone),
  first_name: nome, last_name: sobrenome, itens,
  rastreio: verificarDado(order.track_code), link_rastreio: verificarDado(order.track_url),
  // guard: sem telefone ou sem flow → não dispara
  _skip: !formatarTelefone((customer.phone && customer.phone.full_number) || customer.phone) || !flow_id,
}}];

// ---- BLOCO B: IF "status mudou?" (após Data Table Get) --------------
// condição (n8n IF): {{ $json.statusAlias }}  !=  {{ $('Data Table Get').item.json.status }}
// (se a linha não existe, o campo vem vazio → diferente → dispara. dedup OK)

// ---- BLOCO C: payload do HTTP Request NexTags (specifyBody:'json') ---
// jsonBody =
// {
//   "phone": "={{ $json.phone }}",
//   "first_name": "={{ $json.first_name }}",
//   "last_name": "={{ $json.last_name }}",
//   "actions": [
//     { "action":"set_field_value","field_name":"StatusPedido","value":"={{ $json.statusAlias }}" },
//     { "action":"set_field_value","field_name":"NumeroPedido","value":"={{ $json.order_number }}" },
//     { "action":"set_field_value","field_name":"ProdutosPedido","value":"={{ $json.itens }}" },
//     { "action":"set_field_value","field_name":"RastreioPedido","value":"={{ $json.rastreio }}" },
//     { "action":"add_tag","tag_name":"pedido-={{ $json.statusAlias }}" },
//     { "action":"send_flow","flow_id":"={{ $json.flow_id }}" }
//   ]
// }
// ⚠️ set_field_value SEMPRE antes de send_flow.  Header: X-ACCESS-TOKEN: <NEXTAGS_ACCESS_TOKEN>

// ═══════════════════════════════════════════════════════════════
// TEMPLATE: 1 WORKFLOW POR STATUS
// Use quando a plataforma emite EVENTOS DISTINTOS por status
// (Nuvemshop order/paid, order/fulfilled, fulfillment_order/status_updated;
//  Shopify orders/paid, orders/fulfilled; Martz order.*).
// Ex. produção: Exclusiva (Nuvemshop), Mania Brasil (Martz),
//               Divinnah Gaia (Martz/Shopify), Alto Giro (Shopify).
//
// Cada evento tem SEU webhook. Este template é 1 workflow (ex.: "Pedido Enviado").
// Sem Switch interno — o status é fixo por workflow.
//
// WIRING:
//   Webhook (POST /webhook/{cliente}/{plataforma}/{evento})
//     → [se a plataforma só notifica o ID] HTTP GET detalhe do pedido
//     → Code "Normalizar" (abaixo)
//     → Data Table Get (order_id) → IF já disparou? → NoOp / segue
//     → HTTP Request NexTags (actions[] atômico) → Data Table upsert
// ═══════════════════════════════════════════════════════════════

// (cole os helpers de _helpers.js acima)
const STATUS = 'shipped';                          // <- FIXO por workflow: paid | shipped | delivered
const FLOW_ID = '<FLOW_ID_ENVIADO>';               // <- flow_id REAL do NexTags p/ este status

const body = $input.first().json.body || $input.first().json;
const order = body.resource || body.order || body.data || body;   // ajuste ao payload
const customer = (order.customer && order.customer.data) || order.customer || {};

const order_id = String(order.id || order.order_id);
// Nuvemshop/Shopify: número visível costuma ser order.number / order.name('#123')
const order_number = String(order.number || order.name || order.order_number || order.id).replace('#', '');
const { nome, sobrenome } = separarNomeSobrenome(
  verificarDado(customer.name || ((customer.first_name||'') + ' ' + (customer.last_name||'')), '')
);
const phone = formatarTelefone((customer.phone && customer.phone.full_number) || customer.phone || order.phone);

return [{ json: {
  order_id, order_number, status: STATUS, flow_id: FLOW_ID, phone,
  first_name: nome, last_name: sobrenome,
  rastreio: verificarDado(order.track_code || order.tracking_number),
  link_rastreio: verificarDado(order.track_url || order.tracking_url),
  _skip: !phone,                                    // guard de telefone
}}];

// ---- Data Table de dedup: <Cliente> <Plataforma> Orders State -------
//   colunas: order_id (string) | status (string) | updated_at (string) | customer_phone (string)
//   IF dedup (após Get):  {{ $('DT Get').item.json.status }}  ==  "shipped"  → NoOp (já disparou)
//   senão segue pro HTTP Request e depois upsert (INSERT se novo, UPDATE se existia).
//
// ---- HTTP Request NexTags (specifyBody:'json', retryOnFail, onError:continue) ----
// jsonBody:
// {
//   "phone":"={{ $json.phone }}","first_name":"={{ $json.first_name }}","last_name":"={{ $json.last_name }}",
//   "actions":[
//     {"action":"set_field_value","field_name":"StatusPedidoNS","value":"Enviado"},
//     {"action":"set_field_value","field_name":"NumeroPedidoNS","value":"={{ $json.order_number }}"},
//     {"action":"set_field_value","field_name":"RastreioNS","value":"={{ $json.rastreio }}"},
//     {"action":"send_flow","flow_id":"={{ $json.flow_id }}"}
//   ]
// }
// Header: X-ACCESS-TOKEN: <NEXTAGS_ACCESS_TOKEN>

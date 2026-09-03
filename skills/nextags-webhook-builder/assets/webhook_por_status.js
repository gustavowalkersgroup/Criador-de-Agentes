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
// WIRING (dedup grava SÓ no sucesso — regra nº2):
//   Webhook (POST /webhook/{cliente}/{plataforma}/{evento})
//     → [se a plataforma só notifica o ID] HTTP GET detalhe do pedido
//     → Code "Normalizar + guards" (abaixo)
//     → Data Table Get (order_id | fulfillment_id) → IF "estágio mudou?"
//     → Notificar NexTags (httpRequest, onError: continueErrorOutput)
//     → IF "Notificação OK?"  ({{ $json.error ? 'erro' : 'ok' }} == 'ok')
//          ├─ true  → Salvar Estado (Data Table upsert)   ← só aqui grava dedup
//          └─ false → Falhou (NoOp, NÃO grava)
//
// ⚠️ Gravar o dedup antes/independente do sucesso marca o cliente como
//    notificado para sempre quando a chamada falha (Nordmann v3
//    ln7ZTWGwTyV2KVRQ; Carrinho v2 bvR8NeB5e4BdOzyD: 51 clientes).
// ═══════════════════════════════════════════════════════════════

// (cole os helpers de _helpers.js acima)
const STATUS = 'enviado';                 // <- FIXO por workflow: aprovado | enviado | entregue
const ORIGEM = '<nuvemshop>';             // <- vai no CUF origem_pedido (a plataforma NÃO entra no nome do campo)
const FLOW_ID = 0;                        // <- 0 = fail-safe: NÃO dispara até colocar o flow_id REAL do NexTags

const body = $input.first().json.body || $input.first().json;
const order = body.resource || body.order || body.data || body;   // ajuste ao payload
const customer = (order.customer && order.customer.data) || order.customer || {};

// order_id INTERNO = chave de dedup. Nunca vira CUF.
// Se a plataforma tem envio parcial (Shopify fulfillments), a chave é fulfillment_id (Alto Giro).
const order_id = String(order.id || order.order_id);
const fulfillment_id = String((order.fulfillment && order.fulfillment.id) || order.fulfillment_id || order_id);
// numero_pedido = número VISÍVEL ao cliente, sem '#'
const numero_pedido = String(order.number || order.name || order.order_number || order.id).replace('#', '');

const { nome, sobrenome } = separarNomeSobrenome(
  verificarDado(customer.name || ((customer.first_name || '') + ' ' + (customer.last_name || '')), '')
);

const base = { order_id, fulfillment_id, numero_pedido, status: STATUS };

// ---- guards: telefone (inválido e FIXO) e flow_id ------------------
const g = guardTelefone((customer.phone && customer.phone.full_number) || customer.phone || order.phone);
if (!g.ok) return skip(base, g.motivo);                     // sem_telefone | telefone_invalido | telefone_fixo
if (!FLOW_ID) return skip(base, 'flow_id_ausente:' + STATUS);

return [{ json: {
  ...base,
  flow_id: String(FLOW_ID),
  phone: g.phone,
  first_name: nome,
  last_name: sobrenome,
  email: verificarDado(customer.email, ''),
  // CUFs CANÔNICOS (campos_canonicos.md §5) — snake_case, sem sufixo de plataforma
  origem_pedido: ORIGEM,
  valor_pedido: valorTexto(order.total || order.total_price),
  produtos_pedido: ((order.products && order.products.data) || order.products || order.line_items || [])
    .map(i => `${verificarDado(i.name || i.title)} (Qtd: ${verificarDado(i.quantity)})`)
    .join(', ') || 'Nenhum item',
  rastreio_codigo: verificarDado(order.track_code || order.tracking_number),
  rastreio_url: verificarDado(order.track_url || order.tracking_url),
  rastreio_transportadora: verificarDado(order.shipping_option || order.tracking_company),
  previsao_entrega: verificarDado(order.estimated_delivery || order.shipping_max_days),
}}];

// ---- Data Table de dedup: <Cliente> <Plataforma> Orders State -------
//   colunas: order_id (string) | status (string) | updated_at (string) | customer_phone (string)
//   (use fulfillment_id como chave se a plataforma tem remessa parcial — Alto Giro w1KeVwUnJGdwpidU)
//   IF "estágio mudou?": {{ $json.status }} != {{ $('DT Get').item.json.status }}
//     → compara ESTÁGIO ANTERIOR × NOVO, não "existe linha" (senão Pago bloqueia Enviado/Entregue).
//   Alternativa quando só importa a existência: operação nativa rowNotExists.
//
// ---- HTTP Request NexTags (specifyBody:'json', retryOnFail:true,
//      waitBetweenTries:5000, onError:continueErrorOutput) --------------
// jsonBody:
// {
//   "phone":"={{ $json.phone }}","first_name":"={{ $json.first_name }}",
//   "last_name":"={{ $json.last_name }}","email":"={{ $json.email }}",
//   "actions":[
//     {"action":"set_field_value","field_name":"status_pedido","value":"={{ $json.status }}"},
//     {"action":"set_field_value","field_name":"numero_pedido","value":"={{ $json.numero_pedido }}"},
//     {"action":"set_field_value","field_name":"valor_pedido","value":"={{ $json.valor_pedido }}"},
//     {"action":"set_field_value","field_name":"produtos_pedido","value":"={{ $json.produtos_pedido }}"},
//     {"action":"set_field_value","field_name":"rastreio_codigo","value":"={{ $json.rastreio_codigo }}"},
//     {"action":"set_field_value","field_name":"rastreio_url","value":"={{ $json.rastreio_url }}"},
//     {"action":"set_field_value","field_name":"rastreio_transportadora","value":"={{ $json.rastreio_transportadora }}"},
//     {"action":"set_field_value","field_name":"previsao_entrega","value":"={{ $json.previsao_entrega }}"},
//     {"action":"set_field_value","field_name":"origem_pedido","value":"={{ $json.origem_pedido }}"},
//     {"action":"add_tag","tag_name":"transacional"},
//     {"action":"add_tag","tag_name":"Pedido Enviado"},
//     {"action":"send_flow","flow_id":"={{ $json.flow_id }}"}
//   ]
// }
// ⚠️ Ordem fixa: set_field_value… → add_tag… → send_flow por último.
// Header: X-ACCESS-TOKEN: <NEXTAGS_ACCESS_TOKEN>  (preferir credencial nomeada do n8n)

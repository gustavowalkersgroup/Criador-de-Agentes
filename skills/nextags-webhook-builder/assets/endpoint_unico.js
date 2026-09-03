// ═══════════════════════════════════════════════════════════════
// TEMPLATE: ENDPOINT ÚNICO + SWITCH POR STATUS
// Use quando a plataforma manda 1 evento genérico com status variável
// (Bling pedido_venda.alterado, VTEX, Tray order_changed).
// Ex. produção: Veuske (Yampi), Amo Calçados (Bling), Dolps (VTEX), BB (Tray).
//
// WIRING no n8n (dedup grava SÓ no sucesso — regra nº2):
//   Webhook (POST /webhook/{cliente}/{plataforma}/pedidos)
//     → [se HMAC] Code valida assinatura → responde 200
//     → Code "Normalizar + guards" (bloco A)
//     → Data Table: Get row por order_id  (dedup lookup)
//     → IF "estágio mudou?" (bloco B)
//         ├─ FALSE → NoOp (dedup: já disparado neste estágio)
//         └─ TRUE  → Switch por estágio
//                    → Notificar NexTags (onError: continueErrorOutput)
//                    → IF "Notificação OK?"
//                         ├─ true  → Salvar Estado (Data Table upsert)  ← só aqui
//                         └─ false → Falhou (NoOp, NÃO grava)
//   HTTP Request: retryOnFail:true, waitBetweenTries:5000,
//                 onError:continueErrorOutput, specifyBody:'json'
// ═══════════════════════════════════════════════════════════════

// ---- BLOCO A: normalizar + guards (Code node) ------------------------
// (cole os helpers de _helpers.js acima)
const ORIGEM = '<bling>';        // vai no CUF origem_pedido; NÃO entra no nome dos campos

const body = $input.first().json.body || $input.first().json;
const order = body.resource || body.data || body;                 // ajuste ao payload da plataforma
const customer = (order.customer && order.customer.data) || order.customer || {};

// ⚠️ ESTÁGIO POR ID DE STATUS, NUNCA POR TEXTO.
// A descrição é texto livre que o lojista edita no painel: "Em Entrega" (id 8)
// casava com /entreg/ e virava "entregue", disparando a mensagem errada E gravando
// dedup que bloqueava o Entregue real (id 9). Evidência: Degan BW rroCGCrCnb9R1U5s.
// >>> PREENCHER com os IDs REAIS lidos no painel do cliente e CONFERIDOS contra a API.
const STAGE_BY_STATUS_ID = {
  // '<id_pago>':     'aprovado',
  // '<id_enviado>':  'enviado',
  // '<id_entregue>': 'entregue',
};
const statusId = String(
  (order.status && order.status.id) || order.status_id || order.situacao_id || ''
);
let stage = STAGE_BY_STATUS_ID[statusId] || '';

// Fallback por TEXTO só quando o payload NÃO traz id — e com word-boundary, nunca substring.
if (!stage) {
  const desc = String(
    (order.status && order.status.data && order.status.data.alias) ||
    (order.status && order.status.descricao) || order.status_alias || order.situacao || ''
  ).toLowerCase();
  if (/\bentregue\b/.test(desc)) stage = 'entregue';
  else if (/\benviad[oa]\b|\bdespachad[oa]\b/.test(desc)) stage = 'enviado';
  else if (/\bpag[oa]\b|\baprovad[oa]\b/.test(desc)) stage = 'aprovado';
}

const order_id = String(order.id || order.order_id);                          // INTERNO → dedup
const numero_pedido = String(order.number || order.order_number || order.id).replace('#', ''); // VISÍVEL → CUF
const base = { order_id, numero_pedido, stage, statusId };

// flow_id por estágio — 0 é FAIL-SAFE deliberado: enquanto não tiver o id real,
// o estágio simplesmente não dispara (Degan BW flow_pago/enviado/entregue: 0).
// NUNCA usar id fictício "funcional" (11111111111 / COLE_O_FLOW_ID).
const FLOW_BY_STAGE = {
  aprovado: 0,   // <FLOW_ID_APROVADO>
  enviado:  0,   // <FLOW_ID_ENVIADO>
  entregue: 0,   // <FLOW_ID_ENTREGUE>
  // cancelado: 0,
};
const TAG_BY_STAGE = { aprovado: 'Pedido Aprovado', enviado: 'Pedido Enviado', entregue: 'Pedido Entregue' };

if (!stage) return skip(base, 'estagio_desconhecido:' + statusId);
const flow_id = FLOW_BY_STAGE[stage];
if (!flow_id) return skip(base, 'flow_id_ausente:' + stage);

const g = guardTelefone((customer.phone && customer.phone.full_number) || customer.phone);
if (!g.ok) return skip(base, g.motivo);          // sem_telefone | telefone_invalido | telefone_fixo

const { nome, sobrenome } = separarNomeSobrenome(
  verificarDado((customer.first_name ? customer.first_name + ' ' + (customer.last_name || '') : customer.name), '')
);

return [{ json: {
  ...base,
  flow_id: String(flow_id),
  tag_estagio: TAG_BY_STAGE[stage],
  phone: g.phone,
  first_name: nome,
  last_name: sobrenome,
  email: verificarDado(customer.email, ''),
  // CUFs CANÔNICOS (campos_canonicos.md §5)
  status_pedido: stage,
  origem_pedido: ORIGEM,
  data_pedido: verificarDado(order.date || order.created_at),
  valor_pedido: valorTexto(order.total || order.value),
  qtd_itens_pedido: String(((order.items && order.items.data) || order.items || []).length || 0),
  produtos_pedido: ((order.items && order.items.data) || order.items || [])
    .map(i => `${verificarDado((i.sku && i.sku.data && i.sku.data.title) || i.title)} (Qtd: ${verificarDado(i.quantity)})`)
    .join(', ') || 'Nenhum item',
  rastreio_codigo: verificarDado(order.track_code),
  rastreio_url: verificarDado(order.track_url),
  nota_fiscal: verificarDado(order.invoice_number),
}}];

// ---- BLOCO B: IF "estágio mudou?" (após Data Table Get) --------------
// condição (n8n IF): {{ $json.stage }}  !=  {{ $('Data Table Get').item.json.status }}
// Compara ESTÁGIO ANTERIOR × NOVO (stored.status === stage), não "existe linha":
// o mesmo pedido passa por aprovado → enviado → entregue. (Degan BW)
// Se a linha não existe, o campo vem vazio → diferente → dispara. Dedup OK.
//
// ---- BLOCO C: payload do HTTP Request NexTags (specifyBody:'json') ---
// jsonBody =
// {
//   "phone": "={{ $json.phone }}",
//   "first_name": "={{ $json.first_name }}",
//   "last_name": "={{ $json.last_name }}",
//   "email": "={{ $json.email }}",
//   "actions": [
//     { "action":"set_field_value","field_name":"status_pedido","value":"={{ $json.status_pedido }}" },
//     { "action":"set_field_value","field_name":"numero_pedido","value":"={{ $json.numero_pedido }}" },
//     { "action":"set_field_value","field_name":"data_pedido","value":"={{ $json.data_pedido }}" },
//     { "action":"set_field_value","field_name":"valor_pedido","value":"={{ $json.valor_pedido }}" },
//     { "action":"set_field_value","field_name":"qtd_itens_pedido","value":"={{ $json.qtd_itens_pedido }}" },
//     { "action":"set_field_value","field_name":"produtos_pedido","value":"={{ $json.produtos_pedido }}" },
//     { "action":"set_field_value","field_name":"rastreio_codigo","value":"={{ $json.rastreio_codigo }}" },
//     { "action":"set_field_value","field_name":"rastreio_url","value":"={{ $json.rastreio_url }}" },
//     { "action":"set_field_value","field_name":"nota_fiscal","value":"={{ $json.nota_fiscal }}" },
//     { "action":"set_field_value","field_name":"origem_pedido","value":"={{ $json.origem_pedido }}" },
//     { "action":"add_tag","tag_name":"transacional" },
//     { "action":"add_tag","tag_name":"={{ $json.tag_estagio }}" },
//     { "action":"send_flow","flow_id":"={{ $json.flow_id }}" }
//   ]
// }
// ⚠️ Ordem fixa: set_field_value… → add_tag… → send_flow por último.
// Header: X-ACCESS-TOKEN: <NEXTAGS_ACCESS_TOKEN>  (preferir credencial nomeada do n8n)

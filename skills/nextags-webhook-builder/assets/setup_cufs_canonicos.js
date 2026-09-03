// ═══════════════════════════════════════════════════════════════
// TEMPLATE: SETUP IDEMPOTENTE DE CUFs CANÔNICOS (workflow de setup)
// Inspirado no workflow de setup da Degan (Qwv3YTg9SbVPIqAn).
// Roda UMA vez por conta nova, ANTES de ativar qualquer transacional.
//
// ⚠️ A API NexTags NÃO TEM DELETE de custom field. Nome errado (typo,
//    plural, CamelCase) fica na conta PARA SEMPRE. Por isso o dry-run
//    é obrigatório, não opcional.
// ⚠️ Token é POR CONTA. Token errado retorna 200 e cria os campos na
//    conta errada, sem erro visível (Wazzu com token da Hebreus Doze).
//    Por isso o passo 1 é GET /accounts/me e o nome da conta vai no laudo.
// ⚠️ CUF que já existe com tipo != 0 (Número) DESCARTA o valor em
//    silêncio quando recebe set_field_value (Mayuí; reincidente em Degan).
//    O laudo marca isso como FALHA, não como "já existe".
//
// WIRING no n8n:
//   Manual Trigger
//     → HTTP GET  https://app.nextagsai.com.br/api/accounts/me            ("Conferir Conta")
//     → HTTP GET  https://app.nextagsai.com.br/api/accounts/custom_fields ("Listar Existentes")
//     → Code "Diff" (BLOCO A)
//     → IF  {{ $json.dry_run }} == true
//          ├─ true  → NoOp "LAUDO DRY-RUN"   ← PARE AQUI, humano confere a lista
//          └─ false → Split Out (faltantes)
//                     → HTTP POST /accounts/custom_fields  (um por campo)
//                     → Code "Laudo" (BLOCO B)
//   Header em todos: X-ACCESS-TOKEN: <NEXTAGS_ACCESS_TOKEN>
//   (preferir credencial nomeada do n8n — permite rotação sem editar nodes)
//
// Tags canônicas seguem o mesmo padrão, com GET /accounts/tags/name/{tag_name}
// e POST /accounts/tags {name} — ver BLOCO C.
// ═══════════════════════════════════════════════════════════════

// ---- BLOCO A: diff (Code node "Diff") -------------------------------
// Vire dry_run = false só DEPOIS de conferir o laudo do dry-run.
const DRY_RUN = true;

// Tipos da API: 0 Text | 1 Number | 2 Date | 3 DateTime | 4 Boolean | 5 Long Text | 6 Select | 7 Multi Select
// Regra de ouro: tudo que recebe set_field_value da IA ou do n8n é TEXTO (0).
// Fonte da lista: references/campos_canonicos.md §5 e §7.1. Não invente nome aqui.
const DESEJADOS = [
  // --- handoff / roteamento (conta base) ---
  { name: 'setor_agente',            type: 0 },
  { name: 'tipo_setor',              type: 6 },   // Seleção única: humano | bot
  { name: 'motivo_transferencia',    type: 0 },
  { name: 'prioridade_pipeline',     type: 6 },   // Seleção única: baixa | media | alta
  { name: 'resumo_pipeline',         type: 0 },   // (ou 5 Long Text, se a conta preferir)
  { name: 'resposta_ia',             type: 0 },
  { name: 'data_inicial_pipeline',   type: 3 },
  { name: 'data_vencimento',         type: 3 },
  { name: 'Data_atual',              type: 3 },
  { name: 'horario_atendimento',     type: 0 },
  { name: 'ultimo_atendimento',      type: 0 },

  // --- transacional de PEDIDO (só se houver integração) ---
  { name: 'numero_pedido',           type: 0 },
  { name: 'status_pedido',           type: 0 },
  { name: 'data_pedido',             type: 0 },
  { name: 'valor_pedido',            type: 0 },
  { name: 'qtd_itens_pedido',        type: 0 },
  { name: 'produtos_pedido',         type: 0 },
  { name: 'rastreio_codigo',         type: 0 },
  { name: 'rastreio_url',            type: 0 },
  { name: 'rastreio_transportadora', type: 0 },
  { name: 'previsao_entrega',        type: 0 },
  { name: 'nota_fiscal',             type: 0 },
  { name: 'link_pagamento',          type: 0 },
  { name: 'origem_pedido',           type: 0 },

  // --- transacional de CARRINHO ---
  { name: 'produtos_carrinho',       type: 0 },
  { name: 'valor_carrinho',          type: 0 },
  { name: 'qtd_itens_carrinho',      type: 0 },
  { name: 'link_carrinho',           type: 0 },
];

const conta = $('Conferir Conta').first().json;
const existentes = $input.all()
  .map(i => i.json)
  .flatMap(j => Array.isArray(j) ? j : (j.data || j.custom_fields || [j]))
  .filter(f => f && f.name);

const porNome = new Map(existentes.map(f => [String(f.name).trim(), f]));

const faltantes = [];
const jaExistem = [];
const tipoErrado = [];

for (const d of DESEJADOS) {
  const atual = porNome.get(d.name);
  if (!atual) { faltantes.push(d); continue; }
  if (Number(atual.type) !== Number(d.type)) {
    tipoErrado.push({ name: d.name, esperado: d.type, encontrado: Number(atual.type), id: atual.id });
  } else {
    jaExistem.push({ name: d.name, id: atual.id });
  }
}

// Colisão com legado: campo canônico ausente, mas existe um parecido em CamelCase+sufixo.
// NÃO renomear em cliente rodando (o flow lê o nome antigo) — só reportar.
const legadoSuspeito = existentes
  .filter(f => /^(Status|Numero|Valor|Total|Produtos|Rastreio|Link|Data|QtdItens|PrevisaoEntrega|NotaFiscal)/i.test(f.name))
  .filter(f => !porNome.has(f.name) || !DESEJADOS.some(d => d.name === f.name))
  .map(f => ({ name: f.name, type: Number(f.type), id: f.id }));

return [{ json: {
  dry_run: DRY_RUN,
  conta: { id: conta.id, nome: conta.name },     // ⚠️ CONFIRA que é a conta certa antes de seguir
  total_desejados: DESEJADOS.length,
  ja_existem: jaExistem.length,
  faltantes,                                     // → Split Out alimenta o POST
  tipo_errado: tipoErrado,                       // ⚠️ FALHA: set_field_value descarta em silêncio
  legado_suspeito: legadoSuspeito,               // registrar no relatório, NÃO renomear
  aviso: DRY_RUN
    ? 'DRY-RUN: nada foi criado. Confira faltantes/tipo_errado/legado_suspeito e a conta acima. A API NAO TEM DELETE.'
    : 'EXECUCAO REAL: os campos de faltantes serao criados nesta conta.',
}}];

// ---- HTTP POST de criação (um por item de faltantes) ----------------
// URL:    https://app.nextagsai.com.br/api/accounts/custom_fields
// Body:   specifyBody:'json'  →  { "name": "={{ $json.name }}", "type": {{ $json.type }} }
// Header: X-ACCESS-TOKEN: <NEXTAGS_ACCESS_TOKEN>
// Opções: retryOnFail:true, waitBetweenTries:5000, onError:continueErrorOutput
//         batchSize 1 + intervalo — rate limit NexTags ~100 req/60s (Privilège).
// ⚠️ Campos tipo 6 (Seleção única: tipo_setor, prioridade_pipeline) podem precisar das
//    OPÇÕES cadastradas no painel; conferir depois de criar. O valor gravado tem que
//    bater EXATAMENTE com a opção (minúsculas).

// ---- BLOCO B: laudo final (Code node "Laudo") -----------------------
// const diff = $('Diff').first().json;
// const criados = $input.all().map(i => i.json).filter(r => r && !r.error);
// const falhas  = $input.all().map(i => i.json).filter(r => r && r.error);
// return [{ json: {
//   conta: diff.conta,
//   criados: criados.length,
//   ja_existiam: diff.ja_existem,
//   falhas,
//   TIPO_ERRADO: diff.tipo_errado,        // corrigir no painel: CUF Numero descarta valor em silencio
//   LEGADO: diff.legado_suspeito,         // registrar no relatorio; nao renomear em cliente rodando
//   proximo_passo: 'GET /accounts/flows para validar os flow_id antes de ativar o transacional',
// }}];

// ---- BLOCO C: tags canônicas (mesmo padrão, idempotente) ------------
// const TAGS = ['transacional', 'Pedido Aprovado', 'Pedido Enviado', 'Pedido Entregue'];
// Para cada tag:
//   GET  https://app.nextagsai.com.br/api/accounts/tags/name/{{ $json.tag }}   (existe? pula)
//   POST https://app.nextagsai.com.br/api/accounts/tags   body: { "name": "={{ $json.tag }}" }
// ⚠️ Nomes com maiúscula e espaço são o nome REAL na conta — não normalizar
//    (campos_canonicos.md §4).

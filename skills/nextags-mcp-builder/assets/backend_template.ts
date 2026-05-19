/**
 * TEMPLATE: Backend dedicado (1 operação) — chamado por toolWorkflow do MCP
 *
 * Quando usar: API exige OAuth com refresh (token vivo na data table).
 *              OU operação tem pré-processamento que não cabe em httpRequestTool direto.
 *
 * Padrão: 1 backend = 1 operação. NÃO faça router com switch — workflowInputs
 *         do toolWorkflow não passa valores estáticos (ver quirks_n8n.md).
 *
 * Substitua placeholders <X> antes de validar.
 */

import { workflow, node, trigger, expr } from '@n8n/workflow-sdk';

// === CONFIGURAÇÃO ===
const TOKEN_TABLE_ID = '<id-da-data-table-de-tokens>';  // gerado pelo create_data_table
const STORE_ID = '<store_id-do-cliente>';                // identificador único da loja
const OPERATION_NAME = '<nome-da-operacao>';             // ex: 'buscar_produtos'

// === INPUT do toolWorkflow ===
// Defina APENAS os parâmetros que vêm via $fromAI (1 ou 2 max).
const entrada = trigger({
  type: 'n8n-nodes-base.executeWorkflowTrigger',
  version: 1.1,
  config: {
    name: 'Entrada',
    parameters: {
      inputSource: 'workflowInputs',
      workflowInputs: {
        values: [
          { name: '<input_dinamico>', type: 'string' }  // ex: 'product_id', 'query', 'variant_id'
          // Adicione outros aqui se a operação aceita múltiplos inputs dinâmicos
        ]
      }
    },
    position: [200, 300]
  },
  output: [{ '<input_dinamico>': '<valor de exemplo pra validate>' }]
});

// === LER TOKEN VIVO ===
const lerToken = node({
  type: 'n8n-nodes-base.dataTable',
  version: 1.1,
  config: {
    name: 'Ler Token Vivo',
    parameters: {
      resource: 'row',
      operation: 'get',
      dataTableId: { __rl: true, mode: 'id', value: TOKEN_TABLE_ID },
      matchType: 'allConditions',
      filters: {
        conditions: [{ keyName: 'store_id', condition: 'eq', keyValue: STORE_ID }]
      },
      returnAll: false,
      limit: 1
    },
    position: [460, 300]
  },
  output: [{
    api_host: '<base-url-api>',
    access_token: '<token-sample>'
  }]
});

// === HTTP REQUEST PRA API ===
const httpCall = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: '<API>: <Operação>',
    parameters: {
      method: 'GET',  // ou POST/PUT/DELETE
      url: expr('{{ $json.api_host }}/<endpoint>/{{ $(\'Entrada\').item.json.<input_dinamico> }}'),
      // Se for search/list: usar query params
      // sendQuery: true,
      // specifyQuery: 'keypair',
      // queryParameters: {
      //   parameters: [
      //     { name: '<param>', value: expr('{{ $(\'Entrada\').item.json.<input_dinamico> }}') }
      //   ]
      // },
      sendHeaders: true,
      specifyHeaders: 'keypair',
      headerParameters: {
        parameters: [
          { name: 'Authorization', value: expr('Bearer {{ $json.access_token }}') }
          // Para outras APIs ajustar header (x-api-key, X-VTEX-API-AppKey, etc.)
        ]
      },
      options: { response: { response: { neverError: true } } }
    },
    position: [720, 300]
  }
});

// === SLIM RESPONSE ===
// Ver references/slim_response_patterns.md pra heurísticas detalhadas
const slim = node({
  type: 'n8n-nodes-base.code',
  version: 2,
  config: {
    name: 'Slim Response',
    parameters: {
      mode: 'runOnceForAllItems',
      language: 'javaScript',
      jsCode: `
const body = $input.first().json;

// 1. Tratar erro 4xx/5xx da API
if (body && body.code && body.code >= 400) {
  return [{ json: {
    error: body.causes ? body.causes.join("; ") : body.name || body.message || "API error",
    code: body.code
  }}];
}
if (body && body.error) {
  return [{ json: {
    error: typeof body.error === 'string' ? body.error : (body.error.message || JSON.stringify(body.error)),
    code: body.status || body.statusCode || 500
  }}];
}

// 2. Unwrap (ajustar conforme shape da API)
const items = Array.isArray(body) ? body
  : (body.data || body.list || body.items || body.result || body.Products?.map(x => x.Product || x) || [body]);

// 3. Helper: limpar HTML
const stripHtml = (s) => s ? String(s)
  .replace(/<[^>]+>/g, " ")
  .replace(/&nbsp;/gi, " ")
  .replace(/&[a-z]+;/gi, "")
  .replace(/\\s+/g, " ").trim() : "";

// 4. Extrair só campos essenciais (CUSTOMIZAR POR API)
const slim = items.map(item => ({
  id: item.id,
  name: item.name,
  // ... adicionar campos essenciais conforme a entidade
  // Ver references/slim_response_patterns.md
}));

// 5. Envelope final
return [{ json: {
  total: items.length,
  data: slim
}}];
      `.trim()
    },
    position: [980, 300]
  }
});

export default workflow('<workflow-id-or-empty>', '<API> Backend — <Operação>')
  .add(entrada)
  .to(lerToken)
  .to(httpCall)
  .to(slim);

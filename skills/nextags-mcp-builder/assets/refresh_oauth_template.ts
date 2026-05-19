/**
 * TEMPLATE: Refresh OAuth Token (cron)
 *
 * Renova o access_token antes que expire. Cadência típica: 60 minutos.
 * Se a API tiver access_token mais curto (ex: 1h), ajustar pra 30 min.
 *
 * Padrão: Schedule → Read Data Table → HTTP Refresh → Set → Update Data Table
 *
 * Substitua placeholders <X> antes de validar.
 */

import { workflow, node, trigger, expr } from '@n8n/workflow-sdk';

// === CONFIGURAÇÃO ===
const TOKEN_TABLE_ID = '<id-data-table-tokens>';   // criada com mcp__...__create_data_table
const STORE_ID = '<store_id>';                     // identificador do cliente
const REFRESH_INTERVAL_MIN = 60;                   // 60 min default (ajustar se access_token < 3h)

// === SCHEDULE ===
const cronRefresh = trigger({
  type: 'n8n-nodes-base.scheduleTrigger',
  version: 1.3,
  config: {
    name: `A cada ${REFRESH_INTERVAL_MIN} min`,
    parameters: {
      rule: {
        // Schedule v1.3 limita minutesInterval a 1-59. Pra 60+ usar hours.
        interval: [{ field: 'hours', hoursInterval: 1, triggerAtMinute: 0 }]
      }
    },
    position: [200, 300]
  },
  output: [{ executionMode: 'manual' }]
});

// === LER TOKEN ATUAL ===
const lerToken = node({
  type: 'n8n-nodes-base.dataTable',
  version: 1.1,
  config: {
    name: 'Ler Token Atual',
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
    store_id: STORE_ID,
    api_host: '<api-host>',
    access_token: '<token-velho>',
    refresh_token: '<refresh-velho>'
  }]
});

// === REFRESH TOKEN NA API ===
// CUSTOMIZAR conforme spec da API:
// - Tray: GET {api_host}/auth?refresh_token={refresh} com Bearer {access_token atual}
// - OAuth padrão: POST {token_url} com body {grant_type=refresh_token, refresh_token=X, client_id=Y, client_secret=Z}
const refresh = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: '<API>: Refresh Token',
    parameters: {
      method: 'GET',  // ou POST conforme API
      url: expr('{{ $json.api_host }}/auth'),  // ajustar conforme API
      sendQuery: true,
      specifyQuery: 'keypair',
      queryParameters: {
        parameters: [
          { name: 'refresh_token', value: expr('{{ $json.refresh_token }}') }
        ]
      },
      sendHeaders: true,
      specifyHeaders: 'keypair',
      headerParameters: {
        parameters: [
          { name: 'Authorization', value: expr('Bearer {{ $json.access_token }}') }
        ]
      }
    },
    position: [720, 300]
  },
  output: [{
    access_token: '<token-novo>',
    refresh_token: '<refresh-novo>',
    date_expiration_access_token: '<data>',
    date_expiration_refresh_token: '<data>',
    date_activated: '<data>'
  }]
});

// === MONTAR ROW NOVA ===
// Necessário porque a resposta vem com nomes diferentes dos campos da data table
// Ex: API retorna `date_expiration_access_token` mas data table tem `expires_at`
const montarRow = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'Montar Row Nova',
    parameters: {
      mode: 'manual',
      includeOtherFields: false,
      assignments: {
        assignments: [
          { id: 'a1', name: 'token_value', type: 'string', value: expr('{{ $json.access_token }}') },
          { id: 'a2', name: 'token_refresh', type: 'string', value: expr('{{ $json.refresh_token }}') },
          // Converter formato de data se a API retornar "YYYY-MM-DD HH:mm:ss" (sem TZ)
          // Adicione timezone do cliente conforme o caso
          { id: 'a3', name: 'expires_at', type: 'string', value: expr('{{ $json.date_expiration_access_token.replace(" ", "T") + "-03:00" }}') },
          { id: 'a4', name: 'refresh_expires_at', type: 'string', value: expr('{{ $json.date_expiration_refresh_token.replace(" ", "T") + "-03:00" }}') },
          { id: 'a5', name: 'last_refresh_at', type: 'string', value: expr('{{ $json.date_activated.replace(" ", "T") + "-03:00" }}') }
        ]
      }
    },
    position: [980, 300]
  }
});

// === ATUALIZAR DATA TABLE ===
// ⚠️ CRÍTICO: o campo `columns` é um OBJECT estruturado, não string JSON.
//             Se passar como string, runtime quebra com "Could not get parameter columns.mappingMode"
const atualizarToken = node({
  type: 'n8n-nodes-base.dataTable',
  version: 1.1,
  config: {
    name: 'Atualizar Token na Data Table',
    parameters: {
      resource: 'row',
      operation: 'update',
      dataTableId: { __rl: true, mode: 'id', value: TOKEN_TABLE_ID },
      matchType: 'allConditions',
      filters: {
        conditions: [{ keyName: 'store_id', condition: 'eq', keyValue: STORE_ID }]
      },
      columns: {
        mappingMode: 'defineBelow',
        value: {
          access_token: expr('{{ $json.token_value }}'),
          refresh_token: expr('{{ $json.token_refresh }}'),
          expires_at: expr('{{ $json.expires_at }}'),
          refresh_expires_at: expr('{{ $json.refresh_expires_at }}'),
          last_refresh_at: expr('{{ $json.last_refresh_at }}')
        }
      }
    },
    position: [1240, 300]
  }
});

export default workflow('<workflow-id>', '<API> Refresh Token — <Cliente>')
  .add(cronRefresh)
  .to(lerToken)
  .to(refresh)
  .to(montarRow)
  .to(atualizarToken);

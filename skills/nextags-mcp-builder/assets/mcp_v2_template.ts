/**
 * TEMPLATE: MCP Server Trigger v2 — NexTags
 *
 * Substitua os placeholders <X> antes de validar com mcp__...__validate_workflow.
 *
 * Padrão suportado: tools mistas (httpRequestTool direto + toolWorkflow apontando pra backends).
 *
 * Princípios não-negociáveis (ver references/quirks_n8n.md):
 * - version: 2 OBRIGATÓRIO (v1.1 não conecta com NexTags)
 * - authentication: 'none' por padrão (gate via infra NexTags)
 * - Cada tool tem descrição perfeita (ver references/tool_descriptions_guide.md)
 */

import { workflow, tool, trigger, sticky, newCredential, expr } from '@n8n/workflow-sdk';

// === CONFIGURAÇÃO POR CLIENTE ===
const CLIENT_SLUG = '<slug-cliente-kebab-case>';  // ex: 'mayui-fit-wear-mcp'
const CLIENT_NAME = '<Nome do Cliente>';           // ex: 'Mayuí Fit Wear'

// === CREDENCIAIS (uma por API) ===
const apiCred1 = newCredential('<Nome da API> (chave <cliente>)');
// const apiCred2 = newCredential('<Outra API> (chave <cliente>)');

// === IDs DE BACKENDS (preencher após criar os backends) ===
const BACKEND_OP1 = '<workflow_id_backend_op1>';
// const BACKEND_OP2 = '<workflow_id_backend_op2>';

// === API BASES ===
const API1_BASE = 'https://<base-url-api-1>';
// const API2_BASE = 'https://<base-url-api-2>';

// ============================================
// TOOLS — sigam tool_descriptions_guide.md
// ============================================

/**
 * TIPO A: httpRequestTool direto (auth simples — key fixa)
 *
 * Use quando a API tem auth de header/query estático que não muda.
 * Exemplos: Martz, Nuvemshop, Shopify Admin, RD Station, VTEX.
 */
const toolDireta = tool({
  type: 'n8n-nodes-base.httpRequestTool',
  version: 4.4,
  config: {
    name: '<nome_da_tool>',  // snake_case PT-BR
    parameters: {
      method: 'GET',
      url: API1_BASE + '/<endpoint>',
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',  // ou httpQueryAuth, httpCustomAuth
      sendQuery: true,
      specifyQuery: 'keypair',
      queryParameters: {
        parameters: [
          { name: '<param>', value: expr('{{ $fromAI("<param_ai>", "<descrição clara do que é>", "string") }}') },
          { name: 'per_page', value: '10' }
        ]
      },
      // Slim direto no tool (se shape é conhecido):
      optimizeResponse: true,
      responseType: 'json',
      dataField: '<campo_wrapper>',  // ex: 'data', 'list', 'items'
      fieldsToInclude: 'selected',
      fields: '<campos,separados,por,virgula>'
    },
    credentials: { httpHeaderAuth: apiCred1 },
    position: [520, 80]
    // toolDescription preenche o slot de description do langchain.
    // Para httpRequestTool, configure via UI (não tem prop direto no SDK).
  }
});

/**
 * TIPO B: toolWorkflow → backend dedicado (auth complexo ou OAuth)
 *
 * Use quando há refresh de token ou lógica que precisa rodar antes do HTTP.
 * Cada operação tem seu próprio backend (workflowInputs do toolWorkflow
 * descarta valores estáticos — não dá pra usar router único).
 */
const toolViaBackend = tool({
  type: '@n8n/n8n-nodes-langchain.toolWorkflow',
  version: 2.2,
  config: {
    name: '<nome_da_tool>',
    parameters: {
      description: `<DESCRIÇÃO PERFEITA — siga tool_descriptions_guide.md.

Quando usar: <gatilho concreto com exemplo>.
Quando NÃO usar: <anti-trigger com alternativa>.
Parâmetro: <param> (<formato>). Exemplo: '<valor real>'. <quirk>.
Retorno: <campos>. <quirks importantes do retorno>.`,
      source: 'database',
      workflowId: { __rl: true, mode: 'id', value: BACKEND_OP1 },
      workflowInputs: {
        mappingMode: 'defineBelow',
        value: {
          // ⚠️ APENAS valores que vêm de $fromAI funcionam.
          // Valores estáticos chegam como null no backend.
          // Se precisa de constante (operation, tipo), use 1 backend por valor (1 backend = 1 operação fixa).
          '<param_ai>': expr('{{ $fromAI("<param_ai>", "<descrição>", "string") }}')
        }
      }
    },
    position: [220, 80]
  }
});

// ============================================
// MCP SERVER TRIGGER v2
// ============================================

const mcpTrigger = trigger({
  type: '@n8n/n8n-nodes-langchain.mcpTrigger',
  version: 2,  // ⚠️ OBRIGATÓRIO. v1.1 não conecta com NexTags (só SSE legacy).
  config: {
    name: 'MCP Server Trigger',
    parameters: {
      path: CLIENT_SLUG,
      authentication: 'none'  // padrão. Se cliente exigir, troque pra 'headerAuth' + credencial httpHeaderAuth
      // NÃO use 'bearerAuth' — NexTags não suporta Authorization: Bearer
    },
    subnodes: {
      tools: [
        toolDireta,
        toolViaBackend,
        // ... outras tools
      ]
    },
    position: [200, 400]
  }
});

// ============================================
// STICKY NOTES — documentação inline
// ============================================

const notaArquitetura = sticky(
  '## 🏗 ' + CLIENT_NAME + ' MCP\n\n' +
  '**Endpoint:** `https://nextags.app.br/mcp/' + CLIENT_SLUG + '`\n\n' +
  '<descrever arquitetura: quais APIs, divisão de responsabilidades>\n\n' +
  '**Dependências:**\n' +
  '- <listar backends e auxiliares>',
  [mcpTrigger],
  { color: 6 }
);

// ============================================
// EXPORT
// ============================================

export default workflow('<id-do-workflow-se-update-ou-string-vazia-se-create>', CLIENT_NAME + ' MCP')
  .add(mcpTrigger)
  .add(notaArquitetura);

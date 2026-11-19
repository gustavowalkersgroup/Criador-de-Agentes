# Busca de catálogo ranqueada (identificar peça por descrição ou foto)

Padrão validado em produção (moda, ~1.400 produtos): o agente descreve ou lê a foto de uma peça e uma tool do MCP devolve as fichas mais parecidas, já ranqueadas e diversificadas. Substitui arquivo de base de conhecimento no IA Hub (vector store/arquivos), que o cliente não consegue manter sozinho.

## Quando usar

- Catálogo grande, com peças que se parecem (mesmo modelo em várias cores) e cliente que pede por descrição ou manda foto.
- A busca por nome da API da loja (`buscar_produtos`) não resolve: o cliente não sabe o nome.
- Não usar para preço, estoque, tamanho: isso continua em `obter_produto`.

## Arquitetura (3 workflows, 1 Data Table)

1. **Data Table** `<Cliente> Catalogo Visual`: 1 linha por produto com `product_id`, `name`, `category_name`, `payload_json` (ficha estruturada) e o status da análise.
2. **Workflow de busca** (webhook GET `<cliente>-catalogo-visual`, parâmetros `q`, `tipo`, `limite`): lê a Data Table, um nó Code pontua e ranqueia, responde JSON slim.
3. **Tool no workflow do MCP**: `buscar_catalogo_visual` (`httpRequestTool`) chamando o webhook pela rede interna (`http://n8n:5678/webhook/...`), não pela URL pública.
4. **Workflow de atualização diária** (cron de madrugada): analisa só produtos novos ou alterados, com teto por execução (ex.: 150), e grava na Data Table. Atualização automática é requisito: o cliente não mexe em arquivo.

## Ficha por produto (payload_json)

Gerada por modelo de visão a partir da 1ª imagem + cadastro. Campos usados na busca: `product_type`, `model_or_family`, `silhouette_or_shape`, `pattern_or_print`, `official_color_names` (do cadastro, vale como fato), `observed_colors` (da foto, só apoio), `distinctive_details`, `customer_search_phrases`, `official_description_summary`, `visual_first_image`, `uncertainties`.

Regra: "cadastro" é fato, "na foto" é apoio e pode estar errado. Nunca afirmar material, tamanho ou composição com base só na foto.

## Ranking (Code node)

- Normalizar (minúsculas, sem acento, sem pontuação), tirar stopwords e plural simples ("s" final em palavra > 3 letras).
- Filtro opcional `tipo`: se nenhuma ficha bater, buscar em todo o catálogo e devolver `aviso` (nunca devolver vazio por causa do filtro).
- Pontuar cada termo da consulta em cada campo, com pesos (referência validada): nome 3, tipo 3, modelo 4, formato 2, estampa 2,5, cores do cadastro 3, cores vistas 1,5, detalhes 2, frases do cliente 2, resumo 1, visual 0,7, categoria 1.
- Ordenar por **termos cobertos** primeiro, depois por pontos. Cobrir mais termos vence somar mais pontos num termo só.
- **Diversificar a entrega**: no máximo 3 fichas por modelo (`model_or_family`, senão nome). Sem isso, as 5 vagas viram o mesmo vestido em 5 cores e o agente não tem alternativa para mostrar.
- Devolver slim: id, nome, tipo, modelo, formato, estampa, cores, detalhes, até 2 incertezas, `termos_batidos` ("3 de 4") e pontos. Sem preço, estoque nem tamanho. Incluir `observacao` mandando confirmar com `obter_produto` pelo id.
- Limite padrão 5, máximo 8.

## Roteamento no prompt do agente

Regra curta, sem dado fixo (ver `no_hardcode_with_tools.md`):

- Cliente citou o NOME do produto: `buscar_produtos`.
- Cliente descreveu a peça ou mandou foto (depois de ler a imagem): `buscar_catalogo_visual`, depois `obter_produto` com o id para preço, tamanho, estoque e link.
- Repetir a rota na `description` das duas tools (a do `buscar_produtos` deve apontar para a visual quando a consulta for descrição).
- Achou por foto ou descrição: perguntar na mesma mensagem "é esse modelo, nessa cor?" antes de seguir.

## Armadilhas

- **Agente não chama a tool mesmo com ela ativa no workflow.** Já aconteceu: a descrição no n8n estava certa e o agente seguia sem chamar. O que resolveu foi **recriar o servidor MCP no IA Hub** (Ferramentas de IA → Servidores MCP) e reanexar ao agente. A lista "Allowed tools" do diálogo vem vazia mesmo em servidor novo: é normal, não é sinal de erro. Conferir pelas execuções do webhook de busca no n8n, não pela API (`GET /agents/{id}` devolve `tools: []` mesmo com MCP anexado).
- Ao recriar o servidor, o agente que não precisa da busca (ex.: SAC) pode continuar no servidor antigo; não apagar o antigo sem conferir quem usa.
- Checkpoint da atualização diária: excluir produtos com erro ou análise parcial do reprocessamento diário, senão a mesma imagem quebrada gasta o teto todo dia.
- Produto sem imagem utilizável fica fora da busca visual; listar quantos são para o cliente tratar no cadastro.
- Peça artesanal varia de uma unidade para outra: avisar no prompt.

## Teste

1. Webhook direto: `?q=saia longa vinho cargo&limite=5` devolve fichas coerentes e no máximo 3 por modelo.
2. Webchat (`nextags-webchat-tester`): descrever uma peça em texto e conferir nas execuções do n8n que o webhook foi chamado.
3. Foto real só testa no WhatsApp; webchat é texto.

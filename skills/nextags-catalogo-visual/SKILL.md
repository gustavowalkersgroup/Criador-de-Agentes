---
name: nextags-catalogo-visual
description: "Enriquecimento de catálogos de e-commerce para matching de produtos por texto e imagem: o cliente manda uma foto ou descreve o produto e o bot acha o item certo. Use ao mapear produtos de uma loja, cruzar nomes com atributos visuais e textuais, criar dados para MCP ou bot de vendas, ou retomar grandes lotes com checkpoints e cobertura auditável."
---


# Matching visual de catálogo

Estruture atributos de produtos para recuperar o item certo a partir de descrições em linguagem natural ou fotos. Preserve evidências, nomes e variantes do catálogo; nunca trate cor como identificador único nem invente detalhes ausentes.

## Fluxo de trabalho

### 1. Inventariar e proteger

- Localize o inventário, resultados prévios, arquivos de produto e especificações do MCP/bot, se fornecidas.
- Preserve os arquivos de entrada. Antes de alterações, crie cópia de segurança ou gere artefatos novos versionados.
- Normalize cada item por um ID estável (ID do catálogo; na ausência, índice zero-based original), nome exato, categoria, URL oficial e URL da imagem principal.
- Confira o formato da imagem principal: os canais da NexTags só entregam JPEG e PNG. Imagem em WebP, AVIF, SVG ou GIF vai para `uncertainties` (`formato de imagem não suportado pelos canais`), sem trocar a URL por conta própria.
- Conte registros, detecte IDs/URLs duplicados, variantes e campos ausentes. Gere um manifest com escopo, estado, erros, contagens e arquivos usados.
- Diferencie `analyzed` de `analyzed_with_payload`: só considere análise concluída se atributos/evidências realmente estiverem presentes. Um marcador de execução não é payload analítico.

### 2. Definir escopo e orçamento

- Pergunte/infira o que precisa ser reconhecido pelo bot e quais atributos são discriminativos para aquele catálogo.
- Em execução padrão, analise apenas a primeira imagem principal por item. Consulte galeria, outras imagens, web search ou comparação entre variantes somente se o usuário pedir ou se a primeira imagem/texto forem insuficientes e o orçamento permitir.
- Para catálogos grandes, comece com lote-piloto de 5 itens. Valide a qualidade e o consumo; depois use lotes de 5–8, ajustando ao contexto e orçamento.
- Não paralelize chamadas pesadas sem necessidade. Não inicie serviços pagos, aumente escopo ou consuma orçamento não autorizado.
- Use caching de páginas/imagens e não repita trabalho válido. Se ferramentas de visão não estiverem disponíveis, marque a parte visual como não observada.

### 3. Reunir evidência por item

Para cada item do lote:

1. Leia o registro do inventário e a ficha oficial indicada, se acessível.
2. Use nome, descrição oficial e somente a imagem principal, por padrão.
3. Separe explicitamente fatos textuais do vendedor e observações visuais.
4. Registre cada atributo útil ao matching: tipo, modelo/família, silhueta/forma, estampa/padrão, cores oficiais, cores observadas e detalhes distintivos.
5. Registre frases/sinônimos de busca coloquiais sem convertê-los em fatos de produto.
6. Anote incertezas, inconsistências na página e limitações da imagem. Use `null` quando não houver evidência.
7. Para produtos artesanais, registre avisos de variação de desenho, tonalidade e acabamento. Não prometa que a foto represente toda unidade.
8. Não deduza material, composição, tamanho, fecho, forro, disponibilidade ou preço pela foto. Não confunda elementos cenográficos/modelo com atributos do produto.

A URL, nome e variante originais são chaves de identidade. Corrija categoria apenas com evidência. Preserve números/códigos de variantes mesmo quando os desenhos forem parecidos.

### 4. Formato recomendado

Use JSONL, um objeto independente por produto, para facilitar append, retomada e validação. Adapte o schema ao MCP de destino sem remover a proveniência:

```json
{
  "inventory_index": 213,
  "product_id": null,
  "name": "nome exato do catálogo",
  "category_original": "categoria de origem",
  "category_corrected": null,
  "url": "URL oficial",
  "image_url": "URL da imagem principal analisada",
  "official_description_summary": null,
  "visual_first_image": null,
  "match_attributes": {
    "product_type": null,
    "model_or_family": null,
    "silhouette_or_shape": null,
    "pattern_or_print": null,
    "official_color_names": [],
    "observed_colors": [],
    "distinctive_details": []
  },
  "customer_search_phrases": [],
  "uncertainties": [],
  "evidence": {
    "text_source_url": null,
    "image_source_url": null
  },
  "status": "completed"
}
```

Estados sugeridos: `completed`, `partial_text_only`, `visual_unavailable`, `source_unavailable`, `needs_review`, `not_started`. Não use `completed` para registros com atributos vazios ou só marcador.

### 5. Checkpoint, retomada e falhas

- Salve cada lote imediatamente. Valide JSON por linha antes de avançar; escreva de forma atômica quando regravar arquivos.
- Mantenha `results.jsonl`, `errors.jsonl` e `manifest.json`. O manifest deve listar IDs concluídos com payload válido, pendentes e falhos, lote/índice seguinte, timestamps e caminhos de origem/backup.
- Ao retomar, reabra e valide os arquivos; pule apenas IDs com payload válido. Nunca use memória conversacional como única cópia de resultados.
- Em erro transitório, tente novamente só o item (até um limite pequeno, por exemplo 2 tentativas com espera progressiva). Em 403, CAPTCHA, login ou falta de créditos, registre e siga/parar conforme autorização; não tente contornar o bloqueio.
- Não reinicie lote inteiro por falha de um produto. Não substitua conteúdo válido por placeholders.
- Antes de encerrar por orçamento, salve todos os resultados correntes e informe exatamente quantos itens foram concluídos, pendentes e falhos.

### 6. Matching e validação de qualidade

- Priorize tipo + modelo/família + detalhes estruturais/padrão + variante. Use cor como evidência complementar, nunca como chave única.
- Para consulta visual, identifique primeiro categoria e silhueta, depois estampa e detalhes distintivos; só depois use cor. Se houver candidatos parecidos, mostre alternativas ou peça esclarecimento em vez de afirmar match certo.
- Faça revisão de consistência em pares de variantes: aponte diferenças somente se comprovadas pelas fichas/imagens consultadas. Nomes parecidos não provam que as peças são iguais.
- Valide contagens, chaves únicas, URLs, campos esperados, JSON válido e correspondência entre inventário/resultados.
- Marque `coverage_complete: true` somente se todos os itens do escopo tiverem payload válido. Declare limitações e divergências.
- Entregue o JSON/JSONL para ingestão e um resumo legível com cobertura, regras de matching e casos ambíguos. Não chame metadados de busca vetorial/embeddings se essa etapa não foi implementada.

## Recursos incluídos

- Para transferir o método para Codex ou outro agente de código, use `templates/codex-retomar-catalogo.md` como prompt-base; personalize caminhos, IDs pendentes, ferramentas de visão e orçamento.
- Para auditar um checkpoint JSONL antes de consolidar, execute `scripts/validate_checkpoint.py --help` e informe o inventário e o arquivo de resultados.

## Integração com as outras skills

- O JSONL pronto alimenta o MCP de atendimento: a tool que devolve produto para o bot é construída pela `nextags-mcp-builder` (resposta enxuta, validação de imagem JPEG/PNG).
- Como o bot apresenta o resultado (uma imagem, espera de 2s e botão, ou carrossel com texto antes) está nas regras da `nextags-prompt-creator` e da `nextags-prompt-octobercut`.
- Para subir o prompt do agente depois, use a `nextags-prompt-push`.

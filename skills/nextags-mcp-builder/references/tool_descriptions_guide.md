# Guia de Descrições de Tools — qualidade não-negociável

A descrição de cada tool no MCP é o **único sinal** que o LLM tem pra decidir qual usar. Descrição vaga = LLM escolhe errado, chama tool inadequada, retorna dado ruim, cliente fica confuso. **Descrição perfeita é obrigatório.**

---

## Anatomia de uma descrição perfeita

Toda tool deve responder, na descrição, a 6 perguntas:

| Pergunta | Por quê |
|---|---|
| **O que essa tool faz?** | LLM entende a função |
| **QUANDO usar?** | Gatilho específico (palavras na fala do cliente, contexto) |
| **QUANDO NÃO usar?** | Anti-trigger evita uso errado (mais importante que o trigger) |
| **Quais parâmetros aceita?** | Formato esperado (string? UUID? slug?) com exemplo |
| **O que retorna?** | Campos principais e formato (preço em reais? centavos?) |
| **Quirks/restrições que o LLM precisa saber** | Comportamentos não-óbvios (auto-wildcard, paginação, etc.) |

---

## Exemplos reais (Mayuí)

### ❌ Descrição RUIM

```
"Busca produtos na API."
```

Por que é ruim:
- Não diz QUANDO usar
- Não diz QUE produtos (tem outras tools de produto)
- Não diz o formato do parâmetro
- Não diz o que retorna
- Não menciona quirks

### ✅ Descrição BOA

```
"Busca produtos do catálogo Tray por nome ou parte do nome (LIKE no nome).
Use quando o cliente DISSE explicitamente o nome do produto/coleção
(ex: 'Legging Groove', 'top essence'). Se for busca por cor/categoria
genérica, prefira listar_indice_catalogo antes.

Backend wrappea o termo em %...% automaticamente — passe o texto cru
(ex: 'legging', não '%legging%').

Retorna lista enxuta com id, name, slug, price (em reais, ex '269.90'),
available ('1'=em estoque, '0'=esgotado), image, variant_ids[]."
```

Por que é boa:
- **O que faz:** busca produtos do catálogo Tray
- **QUANDO usar:** cliente disse nome (ex concreto)
- **QUANDO NÃO usar:** se for genérico → outra tool
- **Param:** texto cru, sem wildcards
- **Retorna:** campos com formato (price em reais, available booleano-string)
- **Quirk:** auto-wrap de wildcards

---

## Padrão recomendado (5 parágrafos)

```
[Parágrafo 1: O QUE FAZ]
1 frase descrevendo função. Cite a API fonte se houver mais de uma no MCP.

[Parágrafo 2: QUANDO USAR — com gatilho concreto]
"Use quando o cliente <ação específica>. Exemplos: '<exemplo real 1>', '<exemplo real 2>'."

[Parágrafo 3: QUANDO NÃO USAR — anti-pattern]
"NÃO use se <situação alternativa>. Nesse caso, prefira <outra_tool>."

[Parágrafo 4: PARÂMETROS]
"Parâmetro `X` é <tipo> (<formato esperado, ex: UUID, slug, int>).
Exemplo: '<valor real>'. <Quirk se houver>."

[Parágrafo 5: RETORNO]
"Retorna <wrapper>. Campos principais: <field1> (<formato>), <field2> (<semântica>).
<Quirks importantes do retorno, ex: preço em reais, available '0'=esgotado>."
```

Não precisa seguir literalmente — adapte ao caso. Mas todos os 6 elementos devem estar lá em algum lugar.

---

## Erros comuns a evitar

### 1. Não disambiguar entre tools parecidas

❌ Errado:
```
Tool A: "Busca pedidos"
Tool B: "Lista pedidos"
```

LLM vai chamar aleatório. Solução:
```
Tool A "buscar_pedidos": "Use quando cliente passa texto livre (email, nome, CPF, telefone, número de pedido). Search amplo."
Tool B "listar_pedidos_cliente": "Use quando JÁ TEM o customer_id (UUID, vindo de buscar_cliente). Listagem direta sem busca."
```

### 2. Não documentar formato de IDs

❌ Errado:
```
"customer_id: ID do cliente"
```

✅ Certo:
```
"customer_id: UUID do cliente Martz (formato 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'). DEVE vir do retorno de buscar_cliente. NÃO usar email/telefone/CPF aqui — causa erro 22P02."
```

### 3. Omitir quirks que afetam decisão da IA

❌ Errado:
```
"Busca produtos com filtro de nome"
```

✅ Certo:
```
"Busca produtos com filtro de nome. O backend wrappea com % automaticamente,
passe o termo cru. Search é LIKE — palavra parcial funciona ('legg' acha 'legging')."
```

### 4. Não dizer o que o retorno NÃO traz

Importante quando a IA pode achar que tem info e não tem.

✅ Bom:
```
"Retorna nome, preço, imagens e Variant[] (apenas IDs das variações).
NÃO retorna descrição completa nem estoque por tamanho — use obter_variacao
pra cada variant_id se precisar."
```

### 5. Esquecer dependências entre tools

❌ Errado:
```
Tool: obter_variacao
"Retorna detalhes de uma variação por variant_id."
```

✅ Certo:
```
Tool: obter_variacao
"Retorna detalhes de UMA variação por variant_id. Use APÓS obter_produto,
iterando pelos IDs retornados em Variant[]. Se você não tem o variant_id,
não chame essa tool — chame obter_produto primeiro pra pegar a lista."
```

---

## Como testar se a descrição tá boa

Antes de fechar o MCP, mostre as descrições de TODAS as tools (sem ver o resto do prompt) a um LLM diferente e pergunte:

> "Dado este conjunto de tools com essas descrições, quando o cliente disser
> 'cadê meu pedido?', qual você chamaria primeiro? E se ele disser 'tem
> legging marrom?'? E 'meu email é X, lista meus pedidos'?"

Se o LLM escolher errado, a descrição tem ambiguidade. Refine.

---

## Convenção de naming

Nomes de tools afetam decisão da IA tanto quanto descrição. Padrões:

| Prefixo | Significado | Exemplo |
|---|---|---|
| `buscar_` | Search por texto/filtro (vários resultados) | `buscar_produtos`, `buscar_cliente` |
| `obter_` | Detalhe de UM por ID (1 resultado) | `obter_produto`, `obter_pedido` |
| `listar_` | Listagem com filtro estruturado (vários) | `listar_pedidos_cliente`, `listar_categorias` |
| `criar_` / `atualizar_` | Mutação (se houver) | `criar_lead`, `atualizar_status_pedido` |

Pares "busca/obtém" devem deixar CLARA a diferença:
- `buscar_pedidos(search="texto")` — busca aberta
- `obter_pedido(order_id=UUID)` — drill em 1 específico

Nunca tenha `tool1` e `tool2` com nomes parecidos sem diferença óbvia.

---

## Notas de funcionamento da API (no prompt do agente)

A descrição da tool é o que a IA vê inline ao decidir chamar. Mas o prompt do agente (system message) também deve ter uma seção com **notas de funcionamento das APIs envolvidas**, cobrindo:

- Formato de preço (reais decimal? centavos string? cents number?)
- Formato de IDs (UUID vs int vs slug)
- Semântica de campos booleanos string (`"1"`/`"0"` vs `true`/`false`)
- HTML em descrições (precisa limpar?)
- Idiomas em nomes (Nuvemshop tem `name.pt`/`name.es`)
- Wildcards exigidos (Tray)
- Endpoints que NÃO existem (Martz fantasma)

Exemplo de seção no prompt:

```
## Quirks das APIs

**Tray (catálogo):**
- Preço vem em REAIS com decimal: "269.90" = R$ 269,90. NÃO dividir por 100.
- available="0" = ESGOTADO mas o produto existe (oferece alternativa, NÃO diga "não temos")
- Descrição vem com HTML — o backend já limpa, você recebe texto puro
- Variant[] do produto só traz IDs; pra ver tamanhos use obter_variacao em cada ID

**Martz (pedidos/clientes):**
- IDs são UUID (formato "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"). NUNCA passe int/email/CPF como ID
- Sempre faça buscar_cliente ou buscar_pedidos PRIMEIRO pra obter o UUID
- Preço aqui em CENTAVOS string: "17990" = R$ 179,90. Diferente da Tray.
```

Essa seção evita que a IA confunda formatos quando mistura APIs no mesmo MCP.

---

## Checklist final pra cada tool

Antes de salvar o MCP, valide:

- [ ] Nome é snake_case PT-BR, prefixo certo (buscar/obter/listar/...)
- [ ] Descrição cobre o quê / quando usar / quando NÃO usar / params / retorno / quirks
- [ ] Pelo menos 1 exemplo concreto de fala do cliente no QUANDO USAR
- [ ] Dependência com outras tools explicitada (se houver)
- [ ] Formato de IDs documentado (UUID vs int vs slug)
- [ ] Formato de preço documentado (centavos vs reais)
- [ ] Wildcards/auto-formatação do backend mencionados
- [ ] Lista de tools no MCP NÃO tem 2 com função quase igual sem diferenciação clara

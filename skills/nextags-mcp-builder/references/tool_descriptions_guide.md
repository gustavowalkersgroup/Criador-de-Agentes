# Guia de Descrições de Tools — qualidade não-negociável

A descrição de cada tool no MCP é o **único sinal** que o LLM tem pra decidir qual usar. Descrição vaga = LLM escolhe errado, chama tool inadequada, retorna dado ruim, cliente fica confuso. **Descrição perfeita é obrigatório.**

---

## Anatomia de uma descrição perfeita

Toda tool deve responder, na descrição, a 9 elementos:

| Pergunta | Por quê |
|---|---|
| **O que essa tool faz?** | LLM entende a função |
| **QUANDO usar?** | Gatilho específico (palavras na fala do cliente, contexto) |
| **QUANDO NÃO usar?** | Anti-trigger evita uso errado (mais importante que o trigger) |
| **Quais parâmetros aceita?** | Formato esperado (string? UUID? slug?) com exemplo |
| **O que retorna?** | Campos principais e formato (preço em reais? centavos?) |
| **Quirks/restrições que o LLM precisa saber** | Comportamentos não-óbvios (auto-wildcard, paginação, etc.) |
| **Comportamento em VAZIO** | Retorno vazio = não existe → não inventar, pedir dado correto / ampliar (NÃO é erro) |
| **Comportamento em ERRO** | Falha técnica (`transient:true`) → handoff humano via send_flow, sem expor detalhe técnico |
| **Campos PROIBIDOS / USO INTERNO** | Quais campos a IA NÃO pode exibir (CPF, email, IDs, enum cru) e quais são só classificação interna |

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

## Bloco obrigatório de "comportamento" no fim de cada descrição

Após os 5 parágrafos, anexe um bloco curto de governança que o prompt herda:

```
COMPORTAMENTO:
- Vazio: <o que significa "vazio" aqui> → não inventar; <ação: pedir X / ampliar busca>.
- Erro: instabilidade → não resolver sozinho; encaminhar humano (send_flow), sem detalhe técnico.
- Proibido exibir: <CPF, email, telefone, IDs internos, enum cru de status>.
- Uso interno: <financial_status/fulfillment_status — classificam, nunca aparecem>.
- Encadeia com: <tool seguinte>; copie <cart_id/phash/variant_id> EXATAMENTE como retornado.
- Classe: <leitura | catálogo | transacional | logística-FONTE-DE-VERDADE | cadastro>.
```

Exemplo real (rastreio, fonte-de-verdade de envio):

```
COMPORTAMENTO:
- Vazio: CPF não tem pedido na transportadora → confirmar CPF com o cliente, não dizer "não existe pedido".
- Erro: instabilidade → handoff via send_flow.
- Proibido exibir: tracking interno cru, IDs, financial_status, email/telefone.
- Uso interno: shipment_status cru (já vem traduzido em status_label).
- Encadeia com: nada (folha do pipeline). Recebe phash de listar_pedidos_expedido — use o phash LITERAL.
- Classe: logística-FONTE-DE-VERDADE → para status de ENVIO use SÓ esta tool, NUNCA o fulfillment_status do pedido.
```

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

### Normalização e defaults obrigatórios (pré-chamada)

A descrição deve dizer como o input chega formatado, porque produção trata
omissão/formato errado como erro de chamada:

- Datas: `YYYY-MM-DD` (converter antes de chamar)
- Telefone: com `+` no formato E.164 ao chamar a API (salvar sem `+` se a action exige)
- Número de pedido: remover `#` antes de buscar
- Fuso: SP → UTC = +3h (ISO 8601 com `Z`)
- Email: validar formato ANTES; se mal formatado, pedir pra repetir (não chamar)
- **Defaults obrigatórios:** params como `guests=[]` ou `interesse_produto=''`
  NÃO podem ser omitidos — omissão = erro. Documente o default no schema do
  backend e na descrição: "envie `guests: []` mesmo sem convidados".

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

## Classe semântica da tool (metadado herdado pelo prompt)

Toda tool recebe uma `classe`, emitida no relatório de entrega. O prompt-creator
herda regras automáticas a partir dela:

| Classe | Regra que o prompt herda |
|---|---|
| `leitura` | consultar ANTES de afirmar qualquer fato; não exibir campos crus |
| `catalogo` | consultar antes de citar produto/preço/estoque; retry com termos amplos antes do handoff; entrega pesada (catálogo grande, vários carrosséis, PDF) → delegar a um fluxo via `send_flow`, a IA NÃO monta payload gigante |
| `transacional` (cart/pedido/agendamento) | não inventar link/PIX; em falha → retry 1x + aguardar + degradação (links individuais) |
| `logistica-FONTE-DE-VERDADE` | é a ÚNICA fonte de status de envio/entrega; o prompt NUNCA conclui envio pelo fulfillment_status da plataforma |
| `cadastro/upsert` | params obrigatórios com default (ex: `interesse_produto=''`); omissão = erro |
| `auxiliar/demo` (web/url) | só contexto comercial; sintetizar em 1-2 frases; ZERO URLs cruas |

## Declaração de AUSÊNCIA de capacidade

Se a API NÃO cobre algo que o cliente costuma pedir (cotar frete, calcular
motoboy, segunda via de boleto), o relatório de entrega DEVE listar a frase
pronta pro prompt: *"Não há tool para X — não prometa nem calcule; informe que
o valor/serviço só aparece no checkout / é feito pela equipe."* Trava promessa
que o sistema não cumpre.

## Boilerplate de naming herdado pelo prompt

Os nomes técnicos das tools são INTERNOS. O relatório de entrega inclui:
*"Nunca exponha o nome técnico da tool ao cliente. Fale como humano: 'já tô
buscando isso', 'deixa eu ver aqui'."*

**Coloque a frase também DENTRO da `toolDescription`** (não só no relatório):
*"Nunca cite o nome desta ferramenta para a pessoa."* **[SEM EVIDÊNCIA DIRETA]** — nenhuma
tool do corpus de 21 workflows lidos (Poé incluído) usa essa frase
literalmente; é recomendação por analogia às outras regras de não expor nome técnico (ver
"Boilerplate de naming" acima), não um padrão observado em produção. A descrição é o que o
modelo lê antes de decidir o que responder; repetir ali reduz vazamento de nome técnico em
runtime.

## Regras de domínio que se repetem em produção (adicionar à descrição sempre que se aplicar)

Estas frases aparecem quase literalmente em tool descriptions de clientes diferentes
(evidência: corpus de 21 workflows n8n em produção) — sinal de template interno do time. Inclua a que se
aplicar ao domínio da tool, com a redação do cliente se ele tiver uma mais específica:

| Regra | Quando incluir | Evidência |
|---|---|---|
| "Nunca cite preço/estoque de memória — sempre re-consulte" | qualquer tool de catálogo/estoque | Cantarola: *"NUNCA cite preço de memória."* |
| "Nunca diga a quantidade EXATA em estoque — só disponível/indisponível" | tool que retorna estoque numérico | Degan, repetido em 3 tools |
| "Nunca conclua atraso de entrega por conta própria — você não sabe o prazo prometido a essa pessoa" | tool de rastreio/status de pedido | Degan MCP, repetido 2x |
| "Nunca prometa reembolso, troca, reposição ou data de entrega" | qualquer tool de SAC/pós-venda | padrão geral (Degan, Solentes Net "o agente não decide lente") |
| "Foto só se a extensão for .jpg/.jpeg/.png — outro formato quebra a entrega. Na dúvida, mande só texto" | tool que retorna URL de imagem | Degan |
| "Envelope SEMPRE 200, mesmo em erro — leia `erros[]`/`erro`/`error_code` antes de concluir qualquer coisa" | API que não usa status HTTP pra sinalizar erro (ex.: BW Commerce) | Degan MCP, ver `quirks_n8n.md` Quirk #33 — sem essa frase na description, o agente confunde falha de credencial com "pedido não existe" |
| "Canal atacado não deve ter o total citado como valor final — pode ser renegociado manualmente" | tool de preço/pedido quando o cliente tem canal atacado | Cantarola, 2 tools |
| "Não pergunte diretamente se a pessoa é atacado — leia o campo/etiqueta e infira por perguntas naturais" | tool/prompt que lê perfil de cliente | Cantarola |

Nenhuma dessas é obrigatória em toda tool — aplique a que for pertinente ao domínio da API
que a tool consulta. Quando a API tiver um envelope "sempre-200" ou equivalente
específico, explique o mecanismo exato (não só "leia o erro") — é o que faz o agente
diferenciar corretamente vazio-legítimo de falha técnica.

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
- [ ] Comportamento em VAZIO definido (vazio ≠ erro)
- [ ] Comportamento em ERRO definido (transient → handoff, sem detalhe técnico)
- [ ] Campos PROIBIDOS de exibir listados (CPF, email, telefone, IDs, enum cru)
- [ ] Campos de USO INTERNO marcados (financial_status/fulfillment_status)
- [ ] Classe semântica atribuída (leitura/catalogo/transacional/logistica-FdV/cadastro/auxiliar)
- [ ] Identificadores opacos marcados "copiar exatamente como retornado"
- [ ] Nome técnico aqui == nome citado em qualquer regra/recipe (lint de consistência)
- [ ] Se a API não cobre X comum, frase de ausência gerada pro prompt

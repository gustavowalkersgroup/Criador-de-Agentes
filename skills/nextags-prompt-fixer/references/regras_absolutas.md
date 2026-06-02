# Regras Absolutas NexTags & Padrões de Correção

> Esta referência documenta cada violação que o `analyze_prompt.py` detecta e
> a estratégia de correção apropriada. Use ao consolidar as correções no
> prompt final.

---

## Princípio orientador

**Preservar a função do agente, corrigir só a forma.**

A persona, fluxos, base de conhecimento e regras de negócio são intocáveis.
Você só altera o que viola uma Regra Absoluta da plataforma. Quando uma
correção exigir decisão de produto (qual `flow_id` usar, por exemplo),
**deixe placeholder explícito** e marque como pendente no relatório, em vez
de inventar valor.

---

## 1. JSON inválido (sintaxe)

**Detecção:** o parser do Python falhou ao ler o bloco JSON.

**Como corrigir:**
1. Leia o erro reportado (`syntax_error` no findings) — geralmente é vírgula
   sobrando, aspa não-fechada, chave duplicada ou aspas curvas (`"` em vez de `"`).
2. Reescreva o bloco com sintaxe válida, **mantendo a intenção original**:
   mesmas mensagens, mesmas ações, mesmas tags.
3. Se o conteúdo da mensagem for ambíguo (ex.: um campo cortado no meio),
   **não chute** — marque como pendente e peça revisão humana.

**Antes:**
```json
{"messages":[{"message":{"text":"Olá!",}}]}
```

**Depois:**
```json
{"messages":[{"message":{"text":"Olá!"}}]}
```

---

## 2. Ações proibidas

A plataforma usa fluxos para qualquer transferência ou roteamento. As ações
abaixo **nunca** devem aparecer em JSON gerado pelo agente:

- `transfer_conversation_to`
- `assign_conversation`
- `unassign_conversation`

**Como corrigir:** substitua por `send_flow` apontando para o fluxo de
transferência configurado no projeto.

**Antes:**
```json
{"messages":[{"message":{"text":"Vou te transferir."}}],
 "actions":[{"action":"transfer_conversation_to","value":"human"}]}
```

**Depois:**
```json
{"messages":[{"message":{"text":"Vou te transferir."}}],
 "actions":[{"action":"send_flow","flow_id":"<ID_DO_FLUXO_DE_TRANSFERENCIA>"}]}
```

⚠️ Se o `flow_id` correto não estiver definido no prompt, **mantenha o
placeholder** `<ID_DO_FLUXO_DE_TRANSFERENCIA>` e adicione no relatório:
"⚠️ Definir o ID do fluxo de transferência antes de subir em produção."

---

## 3. Botões sem `web_url`

**Regra:** botões só existem para abrir links externos. Tudo mais (sim/não,
menus, confirmações) deve ser texto simples.

**Detecção do script:** bloco com `template_type: "button"` que tem botão
sem `type: "web_url"` ou sem `url`.

**Como corrigir:**
- Se o botão era para abrir um link externo mas faltou a URL → marque como
  pendente (precisa que alguém forneça a URL).
- Se o botão era pra qualquer outra coisa → **converta o JSON inteiro em
  texto simples**, fazendo a pergunta na própria mensagem e aguardando
  resposta livre do cliente.

**Antes (botão sendo usado como menu — ERRADO):**
```json
{"messages":[{"message":{"attachment":{"payload":{"buttons":[
  {"title":"Sim","type":"postback","payload":"YES"},
  {"title":"Não","type":"postback","payload":"NO"}
],"template_type":"button","text":"Quer prosseguir?"},"type":"template"}}}]}
```

**Depois (texto simples, deixando o cliente responder livre):**
```json
{"messages":[{"message":{"text":"Quer prosseguir? É só me responder com sim ou não."}}]}
```

---

## 4. Carrossel com menos de 2 itens

**Regra:** carrosséis (`template_type: "generic"`) servem para listar 2+
produtos com imagem. Para 1 item, use texto + attachment de imagem.

**Como corrigir:** transforme em uma sequência de mensagens com texto e a
imagem como attachment.

**Antes:**
```json
{"messages":[{"message":{"attachment":{"payload":{"elements":[
  {"title":"Produto X","subtitle":"Descrição","image_url":"https://...","buttons":[]}
],"template_type":"generic","image_aspect_ratio":"horizontal"},"type":"template"}}}]}
```

**Depois:**
```json
{"messages":[
  {"message":{"text":"Produto X — Descrição"}},
  {"message":{"attachment":{"payload":{"url":"https://..."},"type":"image"}}}
]}
```

---

## 5. Markdown dentro do JSON

**Regra:** mensagens são texto puro, como WhatsApp. Nada de `**negrito**`,
`# títulos`, `` `código` `` ou bullets `- item` dentro dos campos `text`,
`subtitle` ou `title`.

**Como corrigir:** retire o markdown e deixe o texto cru. Para ênfase,
prefira reescrever a frase ou usar pausas com mensagens separadas.

**Antes:**
```json
{"messages":[{"message":{"text":"O prazo é **3 a 5 dias úteis**."}}]}
```

**Depois:**
```json
{"messages":[{"message":{"text":"O prazo é de 3 a 5 dias úteis."}}]}
```

---

## 6. Ações proibidas mencionadas em prosa

Mesmo fora de blocos JSON, instruções como "use a ação
`transfer_conversation_to` quando…" são problema, porque podem induzir o
modelo a usá-la em runtime.

**Exceção:** se a menção está em uma seção explicitamente marcada como
"❌ NÃO FAZER" / "PROIBIDO" / "Errado", está tudo bem — o autor está
ensinando o que evitar. O analisador já tenta detectar isso (procura
marcadores como `❌`, `🚫`, `proibido`, `nunca usar` nas linhas anteriores).

**Como corrigir:** quando o analisador apontar uma menção em prosa, leia o
contexto. Se for instrução real, substitua a referência por `send_flow` com
o ID apropriado.

---

## 7. Seções obrigatórias faltando

Um prompt NexTags precisa instruir explicitamente o agente sobre:

| Chave | Por quê |
|---|---|
| `anti_alucinacao` | Sem essa instrução, o modelo vai inventar dados. |
| `nao_revelar_ia` | Cliente não pode saber que é bot — quebra a experiência. |
| `json_obrigatorio` | A plataforma só processa JSON. Texto solto trava o fluxo. |
| `send_flow_transferencia` | Sem isso, o modelo tenta usar ações proibidas. |
| `texto_padrao` | Sem isso, o modelo abusa de botões/carrossel. |
| `fora_de_escopo` | Sem isso, o agente sai do contexto da empresa. |

**Como corrigir:** **não invente** o conteúdo da seção sem confirmar com
quem está usando a skill. Em vez disso:
1. Adicione um placeholder claramente marcado, ex.:

   ```
   ## ⚠️ Seção pendente: Regras anti-alucinação

   <!-- Adicionado automaticamente pelo nextags-prompt-fixer.
        Preencha com as regras anti-alucinação antes de subir em produção. -->

   - Nunca inventar informações que não estejam na base de conhecimento.
   - Nunca assumir dados não confirmados.
   - Quando faltar informação, informar honestamente e disparar fluxo de
     transferência via send_flow.
   ```

2. Liste cada seção pendente no relatório, na seção "Pendências para
   revisão humana".

O objetivo é não deixar o prompt rodar sem essas instruções (risco
operacional alto), mas também não inventar regras de negócio que só o
humano dono do projeto sabe.

---

## 8. Quando NÃO corrigir

Há situações em que a skill deve **flagar e parar** em vez de auto-corrigir:

- Bloco JSON muito complexo cuja intenção não está clara após o erro.
- Conflito entre duas violações que exigem decisões opostas (ex.: tem
  carrossel com 1 item, mas o item tem botão sem URL — qual estratégia
  vence?).
- Texto que parece ser parte da persona/fluxo mas viola alguma regra (pode
  ser intencional pelo autor).
- Casos onde a correção mudaria o comportamento do agente, não só a forma.

Nesses casos: **inclua no relatório com explicação** e deixe a parte
problemática inalterada.

---

## 10. `send_flow` sem `messages` (a regra que NÃO está documentada)

**Regra:** todo JSON de saída que contém `send_flow` em `actions` **precisa** ter o campo `messages` com pelo menos 1 item. Sem `messages`, a plataforma NexTags falha silenciosamente:

- `set_field_value` **roda** ✅
- Tags **rodam** ✅
- `send_flow` **NÃO dispara** ❌

Isso significa que o agente parece estar funcionando (campos preenchidos, tags aplicadas), mas a conversa NUNCA é encaminhada pro fluxo. É a violação mais traiçoeira porque o erro é mudo.

**Detecção:** o `analyze_prompt.py` reporta `send_flow_without_messages_count` quando encontra um bloco JSON com `send_flow` mas sem `messages` (ou com `messages: []`).

**Como corrigir:**

1. Para agentes conversacionais normais: o prompt provavelmente já manda `messages` — esse erro raramente acontece em prompts gerados pelo creator.
2. Para agentes **silenciosos/triadores/classificadores** (que tentam ser puramente actions): adicionar uma **frase de transição curta predefinida por categoria**. Exemplo:

   **Antes (quebra a plataforma — send_flow não dispara):**
   ```json
   {
     "actions": [
       {"action":"set_field_value","field_name":"resumo","value":"..."},
       {"action":"send_flow","flow_id":"123"}
     ]
   }
   ```

   **Depois (funciona):**
   ```json
   {
     "messages": [
       {"message":{"text":"Já vou te conectar com nosso time!"}}
     ],
     "actions": [
       {"action":"set_field_value","field_name":"resumo","value":"..."},
       {"action":"send_flow","flow_id":"123"}
     ]
   }
   ```

⚠️ **Se estiver corrigindo um prompt de agente silencioso e o cliente afirma que o agente não pode falar nada com o usuário:** explique ao cliente que essa frase de transição é exigência da plataforma para o `send_flow` funcionar. Ela é curta, "meta" (só anuncia a transferência, não conversa sobre o problema), e pode ser predefinida — o agente não improvisa. É o menor compromisso possível para destravar o roteamento.

---

## 15. Seções de meta-documentação dentro do prompt

**Regra:** o prompt do agente NUNCA pode conter seções de meta-documentação (auditoria, changelog, pendências internas, TODOs, notas técnicas pra dev, justificativas de decisões passadas, métricas). Tudo isso vai pro **relatório de auditoria**, não pro prompt.

**Por quê:** o prompt é lido pelo LLM A CADA TURNO em runtime. Cada parágrafo que o LLM lê:
- Consome janela de contexto (compartilhada com histórico + tool returns)
- Dilui a atenção do modelo entre o que importa (regras de atendimento) e o que não importa (versões antigas)
- Aumenta custo por turno
- Pode confundir o LLM ("a regra atual é v2.4 ou v2.5?")

Meta-documentação serve só pro humano. Não tem nenhum ganho operacional incluí-la no prompt.

**Padrões a detectar (case-insensitive, em cabeçalhos `#`, `##`, `###`):**

| Padrão | Exemplos |
|---|---|
| `audit(oria)?` | "Auditoria", "Auditoria — Correções v1.0 → v2.0" |
| `changelog` | "Changelog v2.0" |
| `hist[óo]rico\s+de\s+vers[ãa]o` | "Histórico de versões" |
| `vers[ãa]o\s+(anterior|antiga)` | "Versão anterior" |
| `corre[çc][ãa]o(es)?\s+(da|de\s+vers|aplicada)` | "Correções da v2.0", "Correções aplicadas" |
| `pend[êe]ncia(s)?(\s+(interna|humana|pra\s+confirmar))?` | "Pendências internas", "Pendências a confirmar" |
| `\ba\s+confirmar\b` | "A confirmar" |
| `\btodo(s)?\b` (cabeçalho) | "TODO", "TODOs" |
| `notas?\s+(internas?|pra\s+dev|t[ée]cnicas?)` | "Notas internas", "Notas técnicas" |
| `bug(s)?\s+(observad|conhecid)` | "Bugs observados" |
| `m[ée]tric(a|as)\s+do\s+prompt` | "Métricas do prompt" |
| Cabeçalho versionado `v\d+\.\d+\b` | "## v2.5 (correções)" — quando é cabeçalho |

**Heurística adicional:** se um cabeçalho contém "v1.0", "v2.0", "v2.5" e está acompanhado de tabela com "antes/depois" ou "problema/correção", é changelog.

**Cabeçalho do prompt:** uma linha curta tipo `# PROMPT — AGENTE X` está OK. O que NÃO está OK é metadado expandido: `**Versão:** v3.0 | **Data:** Maio/2026 | **Responsável:** Dev X`. Esse metadado vira ruído pro LLM.

**Como corrigir:**

1. Identificar todas as seções que batem nos padrões acima.
2. **Removê-las inteiras** do prompt.
3. **Migrar o conteúdo pro relatório** (`relatorio-<nome>.md`) na seção apropriada:
   - Auditoria/changelog → seção "Histórico de mudanças" do relatório
   - Pendências → seção "Pendências para revisão humana" do relatório
   - Notas técnicas → seção "Notas técnicas / TODO" do relatório
4. **Manter intacto** o que é regra operacional ativa (regras absolutas, fluxos, base de conhecimento, tools).

**Exemplo prático:**

```
# PROMPT — MAYA (WAZZU)
**Versão:** v3.0 enxuta | **Data:** Maio/2026 | **Responsável:** Marcella

## 15. AUDITORIA — CORREÇÕES v1.0 → v2.0 → v2.5
...

## 16. PENDÊNCIAS / A CONFIRMAR
- Pipeline silencioso para produto esgotado: criar flow_id
- Renomear tools com sufixo `1`
```

Vira:

```
# PROMPT — MAYA (WAZZU)
```

(E todo o conteúdo de auditoria/pendência vai pro relatório separado.)

**Princípio:** se o LLM em runtime não precisa daquela informação pra atender uma cliente, ela NÃO pertence ao prompt.

---

## 14. Placeholders genéricos em vez de CUFs nativos

**Regra:** prompts NexTags NUNCA devem usar placeholders genéricos como `[nome]`, `[cliente]`, `[email]`, `[primeiro nome]`, `[telefone]`, `{nome_do_cliente}`, `$first_name$`, `<NOME>`, etc. nos exemplos do prompt. A plataforma NexTags tem um conjunto rico de **Custom User Fields (CUFs)** nativos que são interpolados em runtime — `{{first_name}}`, `{{email}}`, `{{order_id}}`, etc.

**Why:** a plataforma NÃO interpola nada que não seja `{{cuf_real}}`. Qualquer placeholder com colchetes `[ ]`, chaves simples `{ }`, ou cifrões `$ $` aparece literalmente pra cliente — quebrando totalmente a personalização.

**Detecção manual:** procurar por padrões `\[\w+\]`, `\{[a-z_]+\}` (chave única, não dupla), `\$\w+\$`, `<[A-Z_]+>` dentro de campos `text` de exemplos JSON no prompt. Se encontrar, é violação.

**Estratégia de correção:**

1. Identificar o equivalente em `references/cufs_nextags.md` (cobertura completa: contatos, Instagram, Messenger, e-commerce, pedidos).
2. Substituir `[nome]` → `{{first_name}}`, `[email]` → `{{email}}`, `[order_id]` → `{{order_id}}`, etc.
3. Se NÃO existir CUF equivalente (ex: o prompt usa `[código de produto interno]` que não bate com nenhum CUF), **reformule** a frase pra não precisar de interpolação OU marque como pendência humana (talvez precise criar um Custom Field na conta).
4. **Considere fallback:** se substituiu por `{{first_name}}` numa saudação, ofereça variante neutra "sem nome" no caso de cliente sem cadastro:

```
Abertura com nome: {"messages":[{"message":{"text":"Oi, {{first_name}}! Tudo bem?"}}]}
Abertura sem nome: {"messages":[{"message":{"text":"Oi! Tudo bem? Como posso te ajudar?"}}]}
```

**Princípio:** use CUFs SOMENTE quando necessário. Não force `{{first_name}}` em toda mensagem — saudação e momentos-chave bastam.

---

## 13. Prompt inchado (tamanho excessivo)

**Regra:** prompts NexTags ideais ficam entre **15-20 KB**. Acima disso, há quase sempre redundância eliminável. Acima de **30 KB**, considerar revisão agressiva. Acima de **45 KB**, sinal vermelho.

**Por quê:** prompts inchados:
- Desperdiçam context window (compartilhado com histórico + tool returns)
- Aumentam custo por turno
- **Pioram aderência do LLM às regras** — atenção dilui em conteúdo repetido
- Aumentam latência de resposta

**Detecção (manual, não automatizada):**
- `wc -c` no arquivo. >30 KB = revisar.
- Conferir se a mesma regra aparece em múltiplos lugares (ex: "sem markdown" em Regras Absolutas + Regras de Formato + Regras Críticas).
- Conferir se há seções de histórico/changelog/auditoria de versões (v1.0 → v2.0...). Essas NÃO servem ao LLM.
- Conferir se há "pendências internas" / TODOs / notas pro dev — tudo isso deve sair.

**Estratégia de redução (em ordem de impacto):**

1. **Remover seções de auditoria/changelog/histórico de versões.** ~10-15% do peso típico.
2. **Remover "Pendências" / "A confirmar" / notas internas.** Não ajudam o LLM em runtime.
3. **Consolidar fluxos similares.** Troca/Devolução/Defeito/Cancelamento que compartilham 90% da estrutura → UMA seção com tabela de variações. ~15-20% do peso.
4. **Converter prosa em tabela** pra listas de gatilhos, tools, tratamento de erros. ~10% do peso.
5. **Cortar exemplos negativos redundantes.** Manter 2-3 por regra, não 6-8.
6. **Cortar regras duplicadas.** Cada regra é dita UMA vez no lugar mais lógico.
7. **Cortar tools/fluxos/regras herdadas que não se aplicam.** Ex: agente de vendas não precisa de detalhes de política de troca se transfere pra outro agente.
8. **Eliminar palavras de preenchimento** ("obrigatoriamente", "absolutamente", "completamente" repetidos).
9. **Reduzir testes de 8-10 → 4-6 essenciais.**

**Como aplicar (no fluxo do fixer):**

- Medir tamanho atual e reportar no relatório.
- Se >30 KB: sugerir reescrita enxuta como pendência. NÃO refazer automaticamente sem confirmação humana — alta chance de cortar algo que o dono do prompt considera essencial.
- Se >45 KB: marcar como "Diff muito grande — sugerir reescrita do zero" no relatório (já mencionado em "Edge cases" do SKILL.md).

**Princípio:** se uma seção pode ser removida sem mudar o comportamento esperado em runtime, ela DEVE ser removida.

---

## 12. Bloco oficial NexTags ausente

**Regra:** todo prompt de IA da plataforma NexTags Messenger Messaging Platform DEVE conter o bloco oficial de instruções de saída JSON. É um padrão da plataforma, copiado literal.

**Texto canônico do bloco (procurar por estas frases-âncora):**

```
Você é uma IA que deve sempre retornar respostas em JSON válido seguindo o padrão da Messenger Messaging Platform.

Regras:
1 - O JSON deve conter um array "messages" ou um array "actions" (ou ambos).
2 - "messages" é um array de objetos. Cada objeto deve conter um objeto "message".
3 - O objeto "message" deve seguir o schema de mensagens da Messenger Messaging Platform.
4 - Tipos de mensagem suportados:
   - Texto ("text")
   - Texto com botões
   - Imagens
   - Vídeos
   - Carrossel (templates do tipo "generic")
   - Arquivos
5 - Sempre retorne somente JSON válido. Não retornar explicações, comentários, markdown ou qualquer texto fora do JSON.
```

**Detecção:** procurar literalmente pela frase `"deve sempre retornar respostas em JSON válido seguindo o padrão da Messenger Messaging Platform"` (sem acentos opcionais, case-insensitive). Se ausente, é violação.

**Como corrigir:** inserir o bloco LITERAL (sem parafrasear) no início da seção "FORMATO DE RESPOSTA" / "FORMATO DE SAÍDA" / equivalente. Se o prompt não tem essa seção, criar uma seção "FORMATO DE SAÍDA — JSON OBRIGATÓRIO" e colocar o bloco como primeiro conteúdo.

**Por quê:** padronização. Toda IA NexTags responde com o mesmo contrato JSON. Sem o bloco, o agente pode confundir o esquema, especialmente em primeiras chamadas (cache frio). Esse bloco é a especificação canônica que o time NexTags fornece como referência oficial.

**Não substituir nem parafrasear:** o prompt pode ter mais regras adicionais DEPOIS desse bloco, mas o bloco em si vai literal.

---

## 11. Exemplos JSON envolvidos em fences markdown (`` ```json ``)

**Regra:** ao **gerar** um prompt (creator) ou **mostrar exemplos de saída** em qualquer seção do prompt, **NÃO envolva os exemplos JSON em fences de markdown** (`` ```json `` ... `` ``` ``).

**Why:** o LLM em runtime aprende muito mais pelo padrão dos exemplos do que pelas regras textuais. Se cada exemplo de saída esperada está envolvido em fences `` ```json ``, o modelo conclui "JSON sai assim" e copia os fences no output real — fazendo a plataforma tratar tudo como texto e vazar o JSON cru na conversa.

**Detecção manual:** ao revisar/auditar um prompt, conte quantos blocos JSON de exemplo estão dentro de fences `` ```json `` na seção "FORMATO DE RESPOSTA" ou "Exemplos". Se houver fences, isso é uma violação latente (não pega no `analyze_prompt.py` ainda, mas afeta o comportamento em runtime).

**Como corrigir:**

- Remover os `` ```json `` e `` ``` `` antes/depois dos blocos de exemplo.
- Usar separadores de prosa entre exemplos: `— Exemplo 1 — Categoria X:` em texto cru, seguido do JSON diretamente, sem fence.
- O auditor `analyze_prompt.py` continua reconhecendo o JSON pela estrutura (linhas começando com `{`), não precisa de fence pra detectar.

**Princípio geral:** examples > rules. Quando uma regra textual é repetidamente violada apesar de instruções claras, suspeite dos exemplos antes de adicionar mais regras.

---

## 16. Campo `type` dentro de `payload` (erro mais comum em attachments)

**Regra:** em qualquer `attachment`, o campo `type` fica **FORA** de
`payload`, no mesmo nível dele. A plataforma NexTags ignora o `type`
quando ele aparece dentro do `payload` — o middleware não consegue
descobrir que tipo de attachment processar e a mensagem falha.

**Detecção do script:** `analyze_prompt.py` reporta
`type_inside_payload_count` quando encontra `attachment.payload.type`
sem `attachment.type` correspondente.

**Antes (errado — `type` dentro do payload):**
```json
{"messages":[{"message":{"attachment":{"payload":{"type":"image","url":"https://..."}}}}]}
```

**Depois (correto — `type` ao lado do payload):**
```json
{"messages":[{"message":{"attachment":{"type":"image","payload":{"url":"https://..."}}}}]}
```

A mesma regra vale pra templates:
```
✅ {"attachment":{"type":"template","payload":{"template_type":"button",...}}}
❌ {"attachment":{"payload":{"type":"template","template_type":"button",...}}}
```

**Como corrigir:** mover o `type` pra fora do payload, sem alterar mais
nada. É uma transformação puramente estrutural.

---

## 17. Formato de imagem proibido (`.webp`, `.avif`, `.svg`, `.gif`)

**Regra:** a plataforma NexTags entrega imagens nos canais (WhatsApp,
Instagram, Messenger) e **só aceita JPEG e PNG**. Imagens em outros
formatos quebram a entrega em pelo menos um canal.

- ✅ Permitidos: `.jpg`, `.jpeg`, `.png` (Content-Type `image/jpeg` ou `image/png`).
- ❌ Proibidos: `.webp`, `.avif`, `.svg`, `.gif`, `.bmp`, `.tiff`, `.heic`, `.heif`.

**Detecção do script:** `analyze_prompt.py` reporta
`forbidden_image_formats_count` quando encontra URLs em
`payload.url` (attachment image) ou `image_url` (carrossel) com
extensão proibida, ambígua (sem extensão clara) ou não-absoluta.

**Cuidado com CDN.** Muitas CDNs servem `.jpg` na URL respondendo
`Content-Type: image/webp`. A URL parece OK, o canal rejeita. Quando
a extensão é ambígua (`.aspx`, `.php`, sem extensão), o prompt deve
instruir o agente a validar o Content-Type via tool MCP — ou,
preferencialmente, omitir a imagem.

**Como corrigir no prompt:**

1. Se o exemplo de JSON no prompt mostra URL `.webp`/`.avif`/`.svg`/`.gif`:
   substituir pelo placeholder `<URL_JPG_OU_PNG>` ou por uma URL válida.
2. Se o prompt menciona `image/webp` ou WebP como permitido:
   reescrever pra deixar claro que só JPEG/PNG é aceito.
3. Se o prompt usa imagens via tool MCP: incluir as 4 etapas de
   validação de imagem (URL absoluta → extensão → Content-Type → falha
   → omitir). O `prompt_skeleton.md` do creator tem o texto canônico.

**Princípio:** na dúvida sobre formato, REMOVER A IMAGEM. A ausência
da imagem é preferível a quebrar o envio inteiro no canal.

---

## 9. O que JAMAIS alterar

- Nome do agente, persona, tom de voz.
- Conteúdo da base de conhecimento (produtos, preços, políticas).
- Estrutura ou nomes dos fluxos.
- IDs de fluxos, tags, campos personalizados que já estiverem definidos.
- Regras de negócio específicas (ex.: "só ofereça desconto se cliente VIP").
- URLs e mídias já configuradas.
- Idioma, regionalismos, gírias da marca.

Se uma correção exigiria tocar em qualquer uma dessas coisas, ela vira
**pendência humana** automaticamente.

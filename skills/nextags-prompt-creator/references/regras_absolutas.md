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

## 2. Handoff: `send_flow` é o padrão; `transfer_conversation_to`/`assign_conversation` são casos especiais

Todas as 8 ações da plataforma são **válidas** em runtime. O ponto aqui é de
**preferência**, não de proibição:

- **`send_flow` (com `flow_id`) = handoff PADRÃO.** É o mecanismo oficial de
  transferência/roteamento. Sempre que houver um flow configurado, use ele.
- **`transfer_conversation_to` = FALLBACK** quando NÃO há flow de transferência
  configurado no projeto. É rede de segurança, **não é proibida**. Quando der pra
  usar `send_flow`, prefira `send_flow`.
- **`assign_conversation` / `unassign_conversation` = caso especial RARO**
  (atribuir/remover um atendente específico via `admin_id`), definido pelo humano.
  Não sugerir por default, mas **não bloquear** — é válida.

**Como migrar quando faz sentido:** se há flow de transferência configurado e o
prompt usa `transfer_conversation_to` como rota principal, troque por `send_flow`
apontando para o fluxo de transferência do projeto.

**Antes (rota principal, mas há flow configurado):**
```json
{"messages":[{"message":{"text":"Vou te transferir."}}],
 "actions":[{"action":"transfer_conversation_to","value":"human"}]}
```

**Depois (preferir send_flow quando há flow — trio de handoff antes, Regra 21):**
```json
{"messages":[{"message":{"text":"Vou te transferir."}}],
 "actions":[
   {"action":"set_field_value","field_name":"motivo_transferencia","value":"<enum>"},
   {"action":"set_field_value","field_name":"prioridade_pipeline","value":"<baixa|media|alta>"},
   {"action":"set_field_value","field_name":"resumo_pipeline","value":"<2-4 frases>"},
   {"action":"send_flow","flow_id":"<ID_DO_FLUXO_PIPELINE>"}
 ]}
```

⚠️ Se NÃO há flow de transferência configurado, `transfer_conversation_to` é
fallback legítimo — mantenha. Se o `flow_id` correto não estiver definido no
prompt, **mantenha o placeholder** `<ID_DO_FLUXO_PIPELINE>` e adicione no
relatório: "⚠️ Definir o ID do fluxo de pipeline antes de subir em produção."
O trio `motivo_transferencia`/`prioridade_pipeline`/`resumo_pipeline` é
obrigatório antes de todo `send_flow` de transferência — ver Regra 21.

---

## 3. Botões: `web_url` precisa de `url`; limite de 1 link por mensagem

**Regra:**
- Botão `web_url` SEMPRE precisa de `url` (sem `url`, não abre nada).
- **No máximo 1 botão `web_url` por mensagem** (restrição do WhatsApp para link).
- Botão `postback` (dispara um fluxo ao clicar) é **permitido** — podem até 3 —
  mas a IA **raramente** usa. Para sim/não e menus simples, prefira a pergunta em texto.

**Detecção do script (BLOQUEIA):** bloco com `template_type: "button"` que tem
botão `web_url` sem `url`, ou mais de 1 botão `web_url` na mesma mensagem.

**Como corrigir:**
- Botão `web_url` sem `url` → se era pra abrir um link, marque como pendente
  (precisa da URL); se não era um link de verdade, converta em texto simples.
- Para confirmações sim/não → prefira texto simples com a pergunta na própria mensagem.

**Antes (sim/não como botões — prefira texto):**
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

## 5. Markdown dentro do JSON (WA-markup OK; markdown-padrão vaza)

**Regra:** as mensagens renderizam como no WhatsApp.

- **PERMITIDO — marcação estilo WhatsApp:** `*negrito*` (asterisco ÚNICO),
  `_itálico_`, `~tachado~`. Renderiza certinho na plataforma (o cliente testou).
- **PROIBIDO — markdown-PADRÃO (vaza literal):** asterisco-duplo `**bold**`,
  título com hashtag `# título`, link `[texto](url)`, bullets com hífen `- item`,
  e cercas de código (` ``` `). Esses aparecem crus pro cliente.

**Como corrigir:** só o markdown-padrão precisa sair. Troque `**bold**` por
`*bold*` (WA), `[texto](url)` pela URL pura, bullets `-` por quebras de linha
`\n`, e remova `#`/fences. **Não** remova `*negrito*`/`_itálico_`/`~tachado~` —
eles são válidos.

**Antes (asterisco-duplo vaza):**
```json
{"messages":[{"message":{"text":"O prazo é **3 a 5 dias úteis**."}}]}
```

**Depois (WA-markup com asterisco único, OU sem ênfase):**
```json
{"messages":[{"message":{"text":"O prazo é *3 a 5 dias úteis*."}}]}
```

---

## 6. `transfer_conversation_to`/`assign` como ROTA PRINCIPAL em prosa

Como `send_flow` é o handoff padrão (ver §2), instruir o agente a usar
`transfer_conversation_to` como **rota principal de transferência** quando HÁ um
flow configurado é um **aviso de estilo** — convém migrar pra `send_flow`. Não é
proibição: `transfer_conversation_to` continua válido como fallback e
`assign_conversation` como caso especial raro.

**Como ajustar:** se o prompt usa `transfer_conversation_to` como rota principal e
existe flow de transferência, troque a referência por `send_flow` com o `flow_id`
apropriado. Se NÃO há flow configurado, deixe como está — é fallback legítimo.

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

## 10. `send_flow` sem `messages` (transição é OPCIONAL — não falha)

**Regra:** `send_flow` em `actions` **DISPARA NORMALMENTE mesmo sem `messages`** — o
fluxo de bot assume a comunicação a partir dali. **Não é falha silenciosa.** O campo
`messages` é uma **transição OPCIONAL** (curta, por UX), nunca obrigatória.

Comportamento real, com OU sem `messages`:

- `set_field_value` **roda** ✅
- Tags **rodam** ✅
- `send_flow` **DISPARA** ✅

> Correção de regra antiga: versões anteriores diziam que `send_flow` sem `messages`
> "falha silenciosamente / não dispara". Isso está **errado** e foi removido. Disparos
> silenciosos (NPS, mockup, classificadores) são um padrão válido com só `actions`.

**Detecção:** o `analyze_prompt.py` pode reportar `send_flow_without_messages_count`
como **AVISO de estilo** (sugestão de UX: considerar uma transição curta), **nunca**
como violação bloqueante.

**Boa prática de UX (não regra):**

1. Para agentes conversacionais normais: costuma fazer sentido acompanhar o `send_flow`
   de uma transição curta no `messages` ("Já vou te conectar com nosso time!"). É UX, não obrigação.
2. Para agentes **silenciosos/triadores/classificadores**: podem disparar com só `actions` — o fluxo fala. Exemplo perfeitamente válido:

   ```json
   {
     "actions": [
       {"action":"set_field_value","field_name":"resumo","value":"..."},
       {"action":"send_flow","flow_id":"123"}
     ]
   }
   ```

   Se quiser a transição por UX, basta acrescentar `messages` (opcional):

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

⚠️ Se o cliente diz que o agente não pode falar nada com o usuário antes do handoff,
**respeite** — o `send_flow` dispara sozinho e o fluxo conduz. Não force a transição.

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

---

## 21. Campos canônicos de handoff (motivo_transferencia · prioridade_pipeline · resumo_pipeline)

**Regra:** todo agente que transfere para humano gera, no MESMO JSON, antes do
`send_flow` de pipeline: `set_field_value motivo_transferencia` (enum
canônico por setor), `set_field_value prioridade_pipeline`
(`baixa|media|alta`), `set_field_value resumo_pipeline` (2-4 frases), nesta
ordem, com `send_flow` sempre por último. Existe **UM** `<ID_DO_FLUXO_PIPELINE>`
— a fila é decidida pelo VALOR de `motivo_transferencia`, não pelo `flow_id`.
Detalhe completo (enum por setor, critério de prioridade, conteúdo do
resumo, tabela de legado) em `references/campos_canonicos.md` §2, §2.1-§2.4 —
não duplicar aqui.

Enum resumido (minúsculas, sem acento, sem plural): Parcerias
`ugc|colaboracao|influencer|revenda|atacado`; Comercial `vendas|carrinho`;
SAC `rastreio|devolucao|troca|duvida` (`duvida` = catch-all; `sac_geral`
não existe mais). Cada valor que o agente pode usar precisa de ≥1 exemplo
JSON verbatim no prompt gerado.

**A IA NUNCA grava `setor_agente` nem `tipo_setor`** — esses são exclusivos
do Roteador e do Revalidador. Ao gerar o skeleton de um agente (Vendas, SAC,
extras), nunca incluir esses dois campos nas actions de exemplo; a única
transferência que um agente faz é para HUMANO via o trio acima.

Campo stale: os três campos persistem no contato — gerar sempre a regra
explícita ("grave os três em TODA transferência, mesmo repetindo valor")
e nunca um exemplo de `send_flow` sem os três `set_field_value` antes.

---

## 22. Bloco AVISOS ATIVOS e notas para editores

**Regra:** todo prompt de agente gerado (exceto Roteador/Revalidador, que não
levam este bloco) inclui, perto do topo, o bloco `📣 AVISOS ATIVOS` no
formato canônico, vazio por padrão:

```
📣 AVISOS ATIVOS
> 🔧 NOTA PARA EDITORES: edite SÓ as linhas entre os marcadores. Vazio = sem aviso. Remova avisos vencidos.
=== INÍCIO DOS AVISOS ===
(nenhum aviso ativo)
=== FIM DOS AVISOS ===
Se houver aviso acima, considere-o em prazos, disponibilidade e promoções. Se estiver vazio, ignore.
```

Além disso, gerar notas curtas `> 🔧 NOTA PARA EDITORES:` (1 linha, ≤200
caracteres) nos pontos de edição futura provável: AVISOS ATIVOS, tabela de
`motivo_transferencia`, tabela de flow_ids, tabela de tools, bloco DADOS
DESTA CONVERSA, base de conhecimento. Lista completa e frases-modelo em
`references/campos_canonicos.md` §6.1-§6.2.

**Whitelist:** uma linha `> 🔧 NOTA PARA EDITORES:` não é meta-documentação
proibida — é a única forma de nota permitida dentro do prompt gerado. Continua
proibido gerar changelog, versão, pendências, TODO ou justificativas de
decisão dentro do prompt (isso vai só no relatório do creator) — a
whitelist vale só para essa 1 linha curta (≤200 caracteres), nunca para um
parágrafo disfarçado com o mesmo prefixo.

---

## 24. Título de botão: máximo 20 caracteres

**Regra:** todo `title` de botão em template `button` cabe em **20 caracteres**.
Acima disso o passo "Filtro JSON" do fluxo de entrada — o reparador de JSON que
roda entre o agente e o envio — **substitui o título por `"Comprar agora"`**, sem
erro, sem log e sem nada que apareça no painel.

**Por que é bloqueante e não estilo:** o cliente recebe um botão com o texto errado
e ninguém fica sabendo. Num agente de SAC o efeito é grotesco — `"Acompanhar meu
pedido"` (21 caracteres) chega como `"Comprar agora"` embaixo de uma mensagem sobre
devolução. O analisador (`analyze_prompt.py`, check `button_misuse`) bloqueia acima
de 20.

**Alcance:** a troca só pega `payload.buttons` (template `button`). Botão dentro de
`payload.elements[].buttons` (carrossel) **não** passa por ela — mas título curto
continua sendo a regra, porque o botão longo é truncado na tela do WhatsApp de
qualquer jeito.

```json
{"type":"web_url","url":"https://…","title":"Rastrear pedido"}
```

`"Rastrear pedido"` = 15. `"Acompanhar meu pedido"` = 21 → vira `"Comprar agora"`.

> 🔧 NOTA PARA EDITORES: 20 caracteres é limite do fluxo, não preferência de estilo.

(evidência: código do passo "Filtro JSON" em produção, enviado pelo dono em 2026-09-03)

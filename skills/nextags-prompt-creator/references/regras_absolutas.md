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

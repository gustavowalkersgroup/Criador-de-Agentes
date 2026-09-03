# Campos canônicos NexTags — roteamento, handoff, CUFs e etiquetas

> Fonte de verdade ÚNICA do método. Este arquivo é **cópia idêntica** nas skills
> `nextags-prompt-creator`, `nextags-prompt-fixer`, `nextags-mcp-builder` e
> `nextags-webhook-builder`. Alterou aqui, alterou nas quatro.
>
> **Supersede** a seção "🏛️ CUFs de ESCRITA canonicos do metodo" de `cufs_nextags.md`
> (creator/fixer). O que mudou lá: o enum de `motivo_transferencia` virou `duvida` (singular),
> `sac_geral` **deixou de existir**, entraram os valores de parcerias (`ugc`, `colaboracao`,
> `influencer`, `revenda`, `atacado`) e `carrinho`. O resto de `cufs_nextags.md` (CUFs nativos
> de LEITURA, mecânica de interpolação, riscos de campo vazio/stale/injeção) continua válido.

## Como usar este arquivo

- `nextags-prompt-creator` — gera o prompt a partir de §1, §2 e §6; a "LISTA DE FLUXOS E CAMPOS A CRIAR" do relatório sai de §7.
- `nextags-prompt-fixer` — audita contra §2 (ordem das actions, enum, trio de campos), §3 (quem grava o quê) e §6; migra nomes antigos com §8.
- `nextags-mcp-builder` — §1 (quem escreve cada campo, para não duplicar responsabilidade no n8n), §3, §7.5 (criação de CUF/tag por API) e §8.
- `nextags-webhook-builder` — §5 inteiro (CUFs transacionais + telefone fixo), §4 (tags de transacional) e §8 (legado CamelCase que NÃO se renomeia).
- Todas — §9 é lista de dúvidas **em aberto**: repassar ao dono, nunca resolver por conta própria.
- Regra transversal: nome exato, minúsculas, snake_case, sem acento. Só muda se o cliente pedir, e aí a skill registra a exceção no relatório.

---

## 1. Arquitetura canônica de multi-agente (fluxo de entrada)

```
Início (toda mensagem)
  └─ 00 ROTEADOR / "Classificador Inteligente" (passo "Gerar texto" da OpenAI, saída = 1 palavra)
       grava setor_agente = vendas | sac | analisar_humano_bot
       └─ Condição "setor_agente contém …":
            ├─ vendas → Agente Vendas (Gerar texto) → Filtro JSON (Executar código JS)
            │            → grava resposta_ia → passo "Resposta IA vendas" envia {{resposta_ia}}
            ├─ sac    → Agente SAC   (Gerar texto) → Filtro JSON → resposta_ia → "Resposta IA sac"
            └─ else   → REVALIDADOR "Analisar histórico se é bot ou não" (1 palavra)
                          grava tipo_setor = humano | bot
                          ├─ humano → volta para a condição de roteamento (atendimento normal)
                          └─ else (bot) → Arquivar conversa (+ tirar da IA)
                                          → "Seguindo" aguarda 1 hora
                                            (o follow-up NÃO é enviado se o contato responder antes)
                                          → Bloquear contato
```

(evidência: fluxo de entrada em produção — screenshot 1 da rodada 2026-09)

### Regras derivadas

| Regra | Detalhe |
|---|---|
| **O roteador é o único que grava `setor_agente`** | Roda em TODA mensagem lendo o histórico da conversa. Saída texto puro, 1 palavra, minúsculas. Modelo leve (GPT-4.1 nano ou equivalente), temperatura 0. |
| **O revalidador é o único que grava `tipo_setor`** | 2ª camada, só roda no `else`. Fonte `{{chat_history_details_large}}` (200 últimas mensagens com remetente). Saída `humano` \| `bot`. |
| **Nenhuma IA transfere para outra IA** | Agentes (Vendas, SAC, extras) NUNCA gravam `setor_agente` nem `tipo_setor` e NUNCA disparam fluxo que "troca de IA". A única transferência que a IA faz é para HUMANO, via §2. |
| **`resposta_ia` é do FLUXO** | Gravado pelo passo "Filtro JSON" (Executar código JS), nunca pelo prompt. O papel do filtro é **evitar vazamento**: impedir que JSON cru, markdown ou raciocínio da IA cheguem ao cliente. O prompt não menciona esse campo — a IA devolve o JSON canônico NexTags, o filtro extrai o texto e a mensagem sai por `{{resposta_ia}}`. |
| **Ramo bot** | Arquivar conversa (tira da IA) → aguardar 1 hora → bloquear contato. O follow-up de 1h é cancelado se o contato responder antes. |
| **Setores extras** | Cliente com IA própria de Parcerias: o roteador ganha a palavra extra (`parcerias`) e a condição ganha o ramo. Padrão mínimo = `vendas` + `sac`. |

⚠️ O roteador NUNCA responde `analisar_humano_bot` para quem mandou imagem, áudio, arquivo ou
qualquer sinal humano. Na dúvida, roteia para um setor.

⚠️ O valor legado `ignorar` é aceito pelo `else` do fluxo, mas o canônico novo é
`analisar_humano_bot` — **placeholder**: o roteador do dono é um prompt próprio e a palavra exata sai de lá (§9).

### 1.1 Regra de ouro do revalidador

**Na dúvida → `humano`.** A assimetria de risco é o argumento: bot classificado como humano
volta para o fluxo normal e não custa quase nada; humano descartado como bot perde a venda e o
atendimento inteiro. Histórico curto ou vazio → `humano`.

`bot` só se o PADRÃO ao longo do histórico for consistente com máquina: menus numerados /
"selecione uma opção" / confirmações automáticas em MÚLTIPLAS mensagens, nenhuma mensagem com
conteúdo humano real (pergunta, resposta, produto, pedido, nome), gibberish/spam repetido — não
um typo isolado. O texto integral do prompt de referência está no skeleton §8G
(evidência: doc "PROMPT — REVALIDADOR (HUMANO x BOT)", Drive, 2026-07-21).

---

## 2. Handoff IA → humano: UM fluxo de pipeline dirigido por 3 CUFs

A IA, ao decidir transferir, emite no MESMO JSON, **nesta ordem**:

{"messages":[{"message":{"text":"<transição curta na persona>"}}],
 "actions":[
   {"action":"set_field_value","field_name":"motivo_transferencia","value":"<enum>"},
   {"action":"set_field_value","field_name":"prioridade_pipeline","value":"<baixa|media|alta>"},
   {"action":"set_field_value","field_name":"resumo_pipeline","value":"<2 a 4 frases>"},
   {"action":"send_flow","flow_id":"<ID_DO_FLUXO_PIPELINE>"}
 ]}

Depois do `send_flow`: **silêncio total**. A IA não manda mais nada, não pergunta se resolveu,
não faz follow-up.

⚠️ Exemplos de JSON no prompt vão como linhas de texto cru, **nunca dentro de fences
` ```json `**: o modelo copia o fence em runtime e o JSON vaza como texto para o cliente
(evidência: Closet FIT, few-shot dominance).

### 2.0 O que o fluxo de pipeline faz (produção)

```
00 INÍCIO — grava data_inicial_pipeline = agora, Data_atual = agora,
            horario_atendimento = "Segunda a sexta-feira, das 8h às 18h" (texto do cliente)
01 SLA     — data_vencimento = agora + 2h (padrão; cliente pode mudar)
02         — Transferir conversa para humano (tira da IA) + notifica operadores
03 ROTEADOR motivo_transferencia → painel:
   parcerias: ugc | colaboracao | influencer | revenda | atacado  → painel "Parcerias"
   comercial: vendas | carrinho                                    → painel "Comercial"
   sac:       rastreio | devolucao | troca | duvida                → painel "SAC"
   else (valor vazio/desconhecido)                                 → painel "SAC" (mesmo destino de duvida)
   Para cada motivo: "Já existe card aberto?" → SIM: comenta resumo_pipeline no card
                                              → NÃO: cria card (etapa 1 / etapa 2)
   Lê prioridade_pipeline → altera prioridade do card (alta | media | else = baixa padrão)
   COMERCIAL → chama fluxo "Carteira Comercial"; SAC → Round Robin (fallback: admin fixo)
   rastreio  → msg pedindo nº do pedido / CPF / e-mail + {{horario_atendimento}}
   devolucao → msg pedindo pedido / motivo / foto + {{horario_atendimento}}
```

(evidência: fluxo de pipeline em produção — screenshot 2 da rodada 2026-09)

Consequência para o prompt: existe **UM** `flow_id` de transferência, não um por fila. Quem
escolhe a fila é o valor de `motivo_transferencia`, não o `flow_id`.

### 2.1 Enum canônico de `motivo_transferencia`

| Setor / painel | Valor | Quando |
|---|---|---|
| **Parcerias** | `ugc` | criador quer produzir conteúdo em troca de produto |
| | `colaboracao` | proposta de collab / co-marketing / permuta genérica |
| | `influencer` | influenciador pedindo parceria / publi |
| | `revenda` | quer revender / ser representante / lojista |
| | `atacado` | compra em volume / B2B / CNPJ |
| **Comercial** | `vendas` | lead quente pediu humano, exceção comercial, negociação, orçamento |
| | `carrinho` | carrinho/checkout travado, pagamento não concluído, quer fechar com ajuda |
| **SAC** | `rastreio` | pedido, entrega, atraso, extravio, código de rastreio |
| | `devolucao` | quer devolver e receber o dinheiro; arrependimento |
| | `troca` | quer trocar por outro produto / tamanho / cor |
| | `duvida` | **catch-all**: tudo que não é nenhum dos acima (defeito, pagamento, cancelamento, reputacional, jurídico, pergunta sem resposta) |

> 🔧 NOTA PARA EDITORES: não altere estes valores — o fluxo de pipeline filtra estas strings exatas.

- Minúsculas, sem acento, sem plural: `duvida`, não `duvidas`.
- **`sac_geral` não existe mais.** O catch-all é `duvida`, que cai no mesmo destino do `else`.
- **`troca` vs `devolucao`:** usar a palavra da cliente. Quer outra peça → `troca`. Quer o
  dinheiro → `devolucao`. Cancelar antes de receber → `duvida`. Sem regra escrita a IA escolhe
  no chute.
- O fluxo só filtra estas strings. Se o cliente usa outros valores, a skill **pergunta** e
  registra a exceção no relatório.
- **Cada valor do enum que aquele agente pode usar precisa de ≥1 exemplo JSON verbatim no
  prompt.** Enum sem exemplo é enum que a IA erra — a galeria de exemplos é o mecanismo mais
  forte de aderência. Ao gerar, confira a cobertura: valor sem exemplo, escreva um.
- Agente de Vendas costuma usar parcerias + comercial; agente de SAC usa sac. Mas **qualquer
  agente pode usar qualquer valor** (SAC que recebe pedido de revenda grava `revenda`).
- ⚠️ Ao colapsar situações numa tabela, procure linhas AGRUPADAS ("Troca, devolução,
  cancelamento"). Se o enum separa esses casos, a linha agrupada faz a IA escolher no chute —
  precisa split.

### 2.2 `prioridade_pipeline` — `baixa` | `media` | `alta` (Seleção única)

| Valor | Critério padrão (o briefing pode refinar) |
|---|---|
| `alta` | cliente irritado ou ameaçando (Procon, jurídico, reputacional); prejuízo financeiro (pago sem envio, cobrança dupla); prazo vencido; saúde/segurança; lead quente querendo fechar AGORA; atacado/revenda com volume declarado |
| `media` | problema concreto sem urgência (troca, devolução dentro do prazo, atraso curto); lead qualificado que pediu humano; parceria com proposta concreta |
| `baixa` | dúvida geral, informação, parceria genérica sem proposta, lead frio |

Se não souber → `baixa` (é o `else` do fluxo). **Gravar SEMPRE** — o campo persiste, e valor
velho de outro atendimento manda prioridade errada para o card.

### 2.3 `resumo_pipeline` — texto, 2 a 4 frases, sem markdown

Conteúdo obrigatório, **nesta ordem**:

1. Quem é (nome se souber) e os dados que passou (nº do pedido, CPF/e-mail SE já informou, produto/interesse).
2. O problema ou pedido, na palavra do cliente.
3. O que a IA já fez ou tentou (tools consultadas, resposta dada).
4. Por que escalou (o que não conseguiu resolver).

Vai para o comentário/descrição do card no pipeline.

✅ Exemplo bom:
"Leonir, pedido #11488 (R$ 1.538), pago há 12 dias sem despacho. Quer cancelar e reembolso.
Consultei o rastreio: sem movimentação. Não posso cancelar nem reembolsar; escalo irritado."

❌ Exemplo ruim: "Cliente quer falar com humano." — não dá contexto nenhum, o operador começa do zero.

### 2.4 Modo de falha: CAMPO STALE (pior que campo vazio)

Os três campos **persistem no contato**. Transferir sem gravá-los faz o fluxo ler o valor do
atendimento ANTERIOR da mesma pessoa: parece funcionar, mas cai na fila e na prioridade
erradas, e não aparece como erro em lugar nenhum. Campo vazio cai no `else` (aceitável);
campo velho cai no lugar errado (pior).

Por isso, ao gerar ou auditar o prompt:

1. Escrever a regra de gravar os três em TODA transferência, **com a consequência explícita**.
2. Não deixar **nenhum** exemplo de `send_flow` de transferência sem os três `set_field_value` antes.
3. `send_flow` **sempre por último** no array de `actions` (evidência: DOLPS, "Regra 16" — set antes de send, senão os CUFs chegam vazios no destino).
4. **NUNCA** gravar `setor_agente` nem `tipo_setor` num JSON de agente (§3).

---

## 3. Tabela de campos padrão da conta modelo — quem escreve o quê

| Campo | Tipo | Quem grava | Papel / valores |
|---|---|---|---|
| `setor_agente` | Texto | **Roteador** (nunca IA) | `vendas` \| `sac` \| `analisar_humano_bot` (+ setor extra se houver IA extra). Legado: `ignorar`. |
| `tipo_setor` | Seleção única | **Revalidador** (nunca IA) | `humano` \| `bot` |
| `motivo_transferencia` | Texto | **IA**, antes de todo `send_flow` de pipeline | enum §2.1. A descrição oficial na conta ("Resumo que vai pra pipeline") está desatualizada: o campo é o MOTIVO/enum. |
| `prioridade_pipeline` | Seleção única | **IA**, antes de todo `send_flow` | `baixa` \| `media` \| `alta` |
| `resumo_pipeline` | Texto | **IA**, antes de todo `send_flow` | §2.3 |
| `resposta_ia` | Texto | **Fluxo** (passo Filtro JSON) | resposta da IA já filtrada; enviada por `{{resposta_ia}}`. O prompt não menciona. Descrição oficial: "Campo onde a IA vai salvar a resposta depois do card". |
| `data_inicial_pipeline` | Data e hora | **Fluxo de pipeline** | quando o contato foi transferido |
| `data_vencimento` | Data e hora | **Fluxo de pipeline** | SLA do ticket (padrão agora + 2h) |
| `Data_atual` | Data e hora | **Fluxo** | data corrente (uso interno de fluxo) |
| `horario_atendimento` | Texto | **Fluxo** (texto definido pelo cliente) | ex.: "Segunda a sexta-feira, das 8h às 18h"; interpolado nas mensagens de espera |
| `ultimo_atendimento` | Texto | **Fluxo** | salva `{{assigned_admin_name}}` |
| `Nome cliente` | Texto | **não usar** | **não é usado por nenhum fluxo** (confirmado pelo dono, 2026-09-03). O nome do cliente é **sempre** `{{first_name}}` (nativo) — é lá que a IA grava. Se o campo aparecer na conta, ignore. |
| `nota_nps` | Número | **Fluxo de NPS** | nota 0-10 |
| `comentario_nps` | Texto | **Fluxo de NPS** | comentário |
| `sugestao` | Texto | **Fluxo de NPS** | sugestão de melhoria |
| `data_nps` | Data e hora | **Fluxo de NPS** | quando o NPS foi enviado |
| `telefone_capturado` | Texto | **Fluxo Instagram (captura de leads)** | telefone informado no IG |
| `triagem` | Texto | **Fluxo Instagram (captura de leads)** | resultado da triagem |

Regras:

- **Campo de texto livre que recebe `set_field_value` da IA ou do n8n é tipo Texto.** Tipo
  Número descarta o valor **em silêncio**, sem erro (evidência: Mayuí; reincidente em Degan).
- As duas exceções são **Seleção única** na conta modelo: `prioridade_pipeline` e `tipo_setor`.
  Nelas o valor gravado tem que bater EXATAMENTE com a opção cadastrada, minúscula. Valor fora
  da lista é rejeitado — por isso o analyzer bloqueia `prioridade_pipeline` fora de
  `baixa|media|alta`.
- **Campos nativos vão no root do `/api/contacts`, nunca como CUF:** `first_name`, `last_name`,
  `email`, `phone`.
- **Leitura pela IA: a IA só lê o que está ESCRITO no prompt** como `{{campo}}` (mecânica de
  interpolação em `cufs_nextags.md`). Campo populado no contato sem `{{campo}}` no texto do
  prompt = a IA é cega para ele. Campos úteis para o SAC ler: `{{numero_pedido}}`,
  `{{status_pedido}}`, `{{rastreio_url}}`, `{{previsao_entrega}}` — gravados pelos
  transacionais (§5), permitem responder "onde está meu pedido" sem tool quando o transacional
  já populou.

---

## 4. Etiquetas (tags) padrão da conta modelo — quem grava

| Grupo | Tags | Quem grava |
|---|---|---|
| Pipeline / prioridade | `prioridade_alta`, `prioridade_media`, `prioridade_baixa`, `humano` | **Fluxo** (espelha `prioridade_pipeline`; a IA não grava tag de prioridade) |
| Transacional | `transacional`, `Pedido Aprovado`, `Pedido Aprovado 30 dias`, `Pedido Enviado`, `Pedido Entregue` | **n8n** (`add_tag` no mesmo `actions[]` do disparo) |
| NPS | `NPS_enviado`, `feedback_positivo`, `feedback_neutro`, `feedback_negativo` | **Fluxo de NPS** |
| Disparo / broadcast / reativação | `Disparo_recebido`, `Contador de Disparo _ Recebeu`, `contador_disparo_continuar`, `clicou`, `clicou_reativacao`, `clicou no resgatar voucher`, `clicou_em_entrar_no_grupo`, `reativação de base entregue`, `reativação de base falhou`, `Opcao_A`, `Opcao_B`, `Opcao_C`, `Cliente Indicado Promo`, `Cliente Indicado _ Não Participou`, `marcado_para_exclusao` | **Fluxos de campanha / n8n de disparo** |
| Carteira comercial | `Carteira 1`, `Carteira 2`, `Carteira 3`, `Carteira 4` | **Fluxo Carteira Comercial** |
| Instagram | `Captura_leads` | **Fluxo IG** |
| Menu | `NoMenu` | **Fluxo** |

A IA só usa `add_tag` quando o briefing pedir explicitamente. **Prompts não inventam tags.**
Nomes de tag são gravados como estão na tabela (algumas têm maiúsculas e espaços — é o nome
real na conta, não normalizar).

---

## 5. CUFs transacionais canônicos (webhook-builder) — iguais em QUALQUER integração

**A plataforma de origem NÃO entra no nome do campo.** Entra em `origem_pedido`.

| CUF | Conteúdo | Obrigatório em |
|---|---|---|
| `numero_pedido` | número VISÍVEL ao cliente (sem `#`); nunca o id interno | pedido |
| `status_pedido` | `aprovado` \| `enviado` \| `entregue` \| `cancelado` \| `pronto_retirada` \| `pix_expirado` \| `pix_gerado` | pedido |
| `data_pedido` | data legível dd/mm/aaaa | pedido |
| `valor_pedido` | `"379.00"` (ponto decimal, sem R$) | pedido |
| `qtd_itens_pedido` | inteiro como texto | pedido |
| `produtos_pedido` | string legível "Produto (Qtd: 2)" | pedido |
| `rastreio_codigo` | código da transportadora | enviado |
| `rastreio_url` | URL completa de rastreio (com UTM quando for link da loja) | enviado |
| `rastreio_transportadora` | nome da transportadora | enviado (se houver) |
| `previsao_entrega` | data legível | enviado (se houver) |
| `nota_fiscal` | nº/chave da NF | se houver |
| `link_pagamento` | link de checkout/PIX regenerado | pix_gerado / pix_expirado |
| `origem_pedido` | `yampi` \| `shopify` \| `nuvemshop` \| `tray` \| `bagy` \| `bling` \| `vtex` \| `martz` \| `woocommerce` \| `bw` \| … | sempre |
| `produtos_carrinho` | itens do carrinho | carrinho |
| `valor_carrinho` | `"379.00"` | carrinho |
| `qtd_itens_carrinho` | inteiro como texto | carrinho |
| `link_carrinho` | URL de recuperação (com UTM) | carrinho |

Regras:

- **Tudo tipo Texto** (tipo `0` na API). CUF Número descarta o valor em silêncio (evidência: Mayuí).
- **Tags no mesmo `actions[]`** do disparo: `transacional` + `Pedido Aprovado` /
  `Pedido Enviado` / `Pedido Entregue`.
- **Ordem fixa:** `set_field_value`… → `add_tag`… → `send_flow` **por último** (evidência: DOLPS "Regra 16").
- **Legado (`StatusPedidoYMP`, `RastreioPedidoYMP`, `NumeroPedidoBW`, `RastreioNS`,
  CamelCase + sufixo de origem): não criar mais.** Ao auditar fluxo existente, **NÃO renomear**
  — o flow do cliente lê esses nomes. Registrar como legado no relatório. Projeto novo =
  canônico. (evidência dos nomes legados: `padrao_transacional.md` §4-§8.)
- **Multi-plataforma no mesmo contato:** mesmos campos canônicos + `origem_pedido` como
  discriminador; **Data Table de dedup separada por origem** (evidência: Amo Calçados, Bling +
  Loja Integrada).
- **Setup de CUFs por API, idempotente** (padrão Degan): `GET /accounts/custom_fields` → diff →
  `POST /accounts/custom_fields {name, type:0}`. A API **não tem DELETE** → fazer dry-run antes.
- **Token é por conta.** Token errado retorna `200` e cria os campos na conta errada, sem erro
  visível (evidência: Wazzu com token da Hebreus Doze).

### 5.1 Telefone fixo — guard obrigatório antes do disparo

A NexTags **não consegue entregar `send_flow`/mensagem para número FIXO via API**: ao entrar na
plataforma o número ganha o 9 extra e vira inválido (evidência: Alto Giro — ChatRace/NexTags
adiciona `9` cegamente a fixo, `551930000000` vira `5519930000000`).

Regra: **guard antes do disparo** descartando fixo (DDD + 8 dígitos começando em 2-5) +
registrar o descarte no relatório. Nunca "tentar mesmo assim". Vale para o webhook-builder
(guard no Code node) e para o webchat-tester (não usar fixo como contato de teste).

---

## 6. Regras para o prompt (creator / fixer)

### 6.1 Bloco `📣 AVISOS ATIVOS` — sempre, no topo, fácil de editar

Formato fixo (delimitadores claros; o cliente edita SÓ entre as linhas):

```
📣 AVISOS ATIVOS
> 🔧 NOTA PARA EDITORES: edite SÓ as linhas entre os marcadores. Vazio = sem aviso. Remova avisos vencidos.
=== INÍCIO DOS AVISOS ===
(nenhum aviso ativo)
=== FIM DOS AVISOS ===
Se houver aviso acima, considere-o em prazos, disponibilidade e promoções. Se estiver vazio, ignore.
```

### 6.2 Notas para editores (humanos ou outras LLMs) — PEQUENAS

- Marcador único e curto: linha começando com `> 🔧 NOTA PARA EDITORES:` — **1 linha, até ~200
  caracteres**, sem histórico, sem justificativa longa.
- Onde colocar (só onde edição futura é provável):

| Ponto do prompt | Conteúdo típico da nota |
|---|---|
| AVISOS ATIVOS | "edite SÓ as linhas entre os marcadores" |
| Tabela de `motivo_transferencia` | "não altere os valores: o fluxo filtra estas strings" |
| Tabela de flow_ids | "troque só o id, mantenha o nome da chave" |
| Tabela de tools | "nomes vêm do MCP; não renomeie sem mudar o n8n" |
| Bloco DADOS DESTA CONVERSA | "adicione um `{{campo}}` aqui para a IA passar a enxergá-lo" |
| Base de conhecimento | "preço/estoque vêm da tool, não escreva aqui" |

- O analyzer **não** flagra essas linhas como meta-doc (o marcador está na whitelist).
  Continua **proibido** no prompt: changelog, versão, pendências, TODO, justificativas.

### 6.3 Bloco `## DADOS DESTA CONVERSA` (leitura de CUFs)

Sempre gerar, logo após IDENTIDADE/AVISOS:

```
## DADOS DESTA CONVERSA (uso interno — nunca liste de volta para o cliente)
Nome: {{first_name}} · Telefone: {{phone}} · E-mail: {{email}} · Hora local: {{current_user_time}}
{SE SAC/transacional} Último pedido: {{numero_pedido}} · Status: {{status_pedido}} · Rastreio: {{rastreio_url}} · Previsão: {{previsao_entrega}}
{CUFs específicos da conta que a IA precisa para decidir}
> 🔧 NOTA PARA EDITORES: a IA só enxerga campo escrito aqui como {{campo}}. Campo vazio = ignorar.
```

**Regra do nome:** se `{{first_name}}` estiver vazio, for `"Guest"` (webchat) ou não parecer
primeiro nome de pessoa (frase, empresa, expressão) → saudação neutra + perguntar o nome **UMA
vez** → gravar:

{"actions":[{"action":"set_field_value","field_name":"first_name","value":"<nome>"}]}

Não repetir a pergunta se a pessoa não responder.

---

## 7. Checklist de conta nova (copiar e colar)

### 7.1 CUFs a criar (`POST /accounts/custom_fields {name, type}`)

```
[ ] setor_agente            Texto (0)
[ ] tipo_setor              Seleção única (6) — opções: humano, bot
[ ] motivo_transferencia    Texto (0)
[ ] prioridade_pipeline     Seleção única (6) — opções: baixa, media, alta
[ ] resumo_pipeline         Texto (0)   (ou Long Text (5) se a conta preferir)
[ ] resposta_ia             Texto (0)
[ ] data_inicial_pipeline   Data e hora (3)
[ ] data_vencimento         Data e hora (3)
[ ] Data_atual              Data e hora (3)
[ ] horario_atendimento     Texto (0)
[ ] ultimo_atendimento      Texto (0)
[ ] nota_nps                Número (1)      (só fluxo de NPS escreve)
[ ] comentario_nps          Texto (0)
[ ] sugestao                Texto (0)
[ ] data_nps                Data e hora (3)
[ ] telefone_capturado      Texto (0)       (só se houver captura por Instagram)
[ ] triagem                 Texto (0)       (só se houver captura por Instagram)
Transacional (só se o cliente tiver integração de pedido/carrinho) — TODOS Texto (0):
[ ] numero_pedido  [ ] status_pedido  [ ] data_pedido  [ ] valor_pedido
[ ] qtd_itens_pedido  [ ] produtos_pedido  [ ] rastreio_codigo  [ ] rastreio_url
[ ] rastreio_transportadora  [ ] previsao_entrega  [ ] nota_fiscal  [ ] link_pagamento
[ ] origem_pedido  [ ] produtos_carrinho  [ ] valor_carrinho  [ ] qtd_itens_carrinho
[ ] link_carrinho
```

Tipos da API: `0` Text, `1` Number, `2` Date, `3` DateTime, `4` Boolean, `5` Long Text,
`6` Select, `7` Multi Select.

### 7.2 Tags a criar (`POST /accounts/tags {name}`)

```
[ ] prioridade_alta  [ ] prioridade_media  [ ] prioridade_baixa  [ ] humano
[ ] transacional  [ ] Pedido Aprovado  [ ] Pedido Enviado  [ ] Pedido Entregue   (se transacional)
[ ] NPS_enviado  [ ] feedback_positivo  [ ] feedback_neutro  [ ] feedback_negativo   (se NPS)
[ ] Carteira 1..4   (se houver carteira comercial)
[ ] Captura_leads   (se houver captura por Instagram)
[ ] NoMenu
```

### 7.3 Fluxos a criar

```
[ ] Fluxo de ENTRADA (roda em toda mensagem) — roteador + condição por setor_agente
    + ramo else → revalidador → arquivar / aguardar 1h / bloquear   (§1)
[ ] Passo "Filtro JSON" (Executar código JS) em cada ramo de agente → grava resposta_ia
[ ] Fluxo de PIPELINE (UM só) — 00 INÍCIO / 01 SLA / 02 transferir / 03 roteador por
    motivo_transferencia + prioridade + card + Carteira Comercial | Round Robin   (§2.0)
[ ] Fluxo de NPS (nota_nps, comentario_nps, sugestao, data_nps + tags de feedback)
[ ] Fluxos transacionais no n8n (se houver integração)   (§5)
[ ] Validar todo flow_id real com GET /accounts/flows ANTES de escrever no prompt
```

### 7.4 Prompts a gerar

```
[ ] ROTEADOR      — 1 palavra, texto puro, sem JSON, sem tools   (skeleton §8F)
[ ] REVALIDADOR   — 1 palavra (humano|bot), sem JSON, sem tools  (skeleton §8G)
[ ] AGENTE(S)     — Vendas, SAC (+ extras): JSON canônico NexTags, seção de transferência
                    completa (§2), AVISOS ATIVOS (§6.1), DADOS DESTA CONVERSA (§6.3)
```

O relatório do creator entrega isso como **"LISTA DE FLUXOS E CAMPOS A CRIAR"**.

### 7.5 Como criar por API

- Listar antes de criar (idempotente, padrão Degan): `GET /accounts/custom_fields` → diff → criar só o que falta.
- Criar CUF: `POST /accounts/custom_fields` com `{"name":"motivo_transferencia","type":0}`.
- Criar tag: `POST /accounts/tags` com `{"name":"transacional"}`; consultar por nome em `GET /accounts/tags/name/{tag_name}`.
- Validar flow: `GET /accounts/flows` — **o `flow_id` precisa existir de verdade**;
  `/send/{flow_id}` retorna `success:true` até para id inexistente (evidência: Alto Giro).
- Base: `https://app.nextagsai.com.br/api/`, header `X-ACCESS-TOKEN`.
- ⚠️ A API **não tem DELETE** de custom field. Dry-run primeiro; nome errado fica para sempre.
- ⚠️ Token é por conta. Conferir a conta antes de rodar o setup (evidência: Wazzu/Hebreus Doze).

---

## 8. Legado e migração

| Legado (nome / valor) | Canônico | Observação |
|---|---|---|
| `duvidas` | `duvida` | singular, sem plural |
| `sac_geral` | `duvida` | o catch-all agora é `duvida`, mesmo destino do `else` |
| `ignorar` (roteador) | `analisar_humano_bot` (placeholder) | `ignorar` ainda é aceito pelo `else` do fluxo; palavra final vem do prompt do roteador (§9) |
| `agente_setor` | `setor_agente` | nome invertido em docs antigas |
| `StatusPedidoYMP` | `status_pedido` + `origem_pedido: yampi` | CamelCase + sufixo de plataforma |
| `RastreioNS` / `RastreioPedidoYMP` | `rastreio_url` (e `rastreio_codigo`) | separar código de URL |
| `NumeroPedidoBW` / `NumeroPedidoBling` / `NumeroPedidoShopify` | `numero_pedido` + `origem_pedido` | a origem sai do nome e vira campo |
| `OrigemPedido` | `origem_pedido` | snake_case |
| `assunto_ticket` / `resumo_lead` / `sac_resumo` | `resumo_pipeline` | um resumo só, §2.3 |
| `sac_prioridade` | `prioridade_pipeline` | valores `baixa\|media\|alta` |
| `sac_categoria` | `motivo_transferencia` | enum §2.1 |
| N flows dedicados IA↔IA (padrão Veuske) | 1 roteador por mensagem | §8.1 abaixo |

⚠️ **Regra dura: nunca renomear campo em cliente rodando sem atualizar o fluxo junto.** O flow
de produção filtra pelo nome/valor antigo; renomear o CUF sem tocar no flow quebra o
roteamento em silêncio (o disparo retorna sucesso e não faz nada). Em auditoria de cliente
existente: registrar como legado no relatório, migrar só em janela combinada, campo e flow na
mesma mudança.

### 8.1 Legado IA↔IA: o padrão Veuske (`handoff_pattern.md`) e por que foi abandonado

O padrão anterior (Veuske/Rafa, 2026-06-04) resolvia "qual AGENTE IA atende" com **N flows
dedicados, 1 por destino**: o agente gravava `resumo_pipeline` e disparava um flow de destino,
e **esse flow** gravava `setor_agente`. Foi abandonado porque `setor_agente` é relido pelo
fluxo de entrada a CADA mensagem: valor que não bate com nenhum branch cai no default, e
default apontando para uma IA fecha o ciclo — loop infinito de transferência em produção
(evidência: Veuske, `setor_agente=PEDRO` no router com o prompt do Pedro gravando `humano`;
o quirk "flow router que reseta `setor_agente`" em `quirks_n8n.md` da `nextags-mcp-builder` continua válido como explicação do bug). O canônico substitui
tudo isso por **um roteador único que roda a cada mensagem** e é o único escritor de
`setor_agente` (§1): nenhuma IA transfere para IA, some a classe inteira de bug. `resumo_pipeline`
deixa de ser contexto de handoff IA↔IA e passa a ser o resumo que vai para o card do pipeline
(§2.3).

---

## 9. Definições do dono — o que está fechado e o que falta

### Confirmado (2026-09-03)

- **`Nome cliente` não é usado.** O nome do cliente é **sempre** `{{first_name}}` (nativo).
  A IA grava lá; nenhum fluxo lê o CUF `Nome cliente`.
- **Enum de `status_pedido`** (transacional): `aprovado`, `enviado`, `entregue`, `cancelado`,
  `pronto_retirada`, `pix_gerado`, `pix_expirado`. Fechado — é o enum canônico (§5).
- **O que é o passo "Filtro JSON":** um nó de código **JavaScript** cujo papel é **evitar
  vazamento** — impedir que JSON cru, markdown ou raciocínio da IA cheguem ao cliente.
  Confirma o desenho descrito aqui: o prompt devolve o JSON canônico NexTags, o filtro
  extrai o texto e grava `resposta_ia`, e o prompt **nunca** menciona esse campo.

### Ainda aberto — NÃO chutar

1. **Roteador:** o dono vai mandar o **prompt** do roteador; a terceira palavra sai de lá.
   Até chegar, `analisar_humano_bot` é placeholder — **confirme antes de gerar o fluxo**,
   e registre a pendência no relatório.
2. **Caminho do relatório MCP por cliente** (`Z:\WALKERS\<cliente>\`) — o dono vai passar.

Enquanto não houver resposta, as skills usam o placeholder acima e **marcam a pendência no
relatório**; nenhuma skill decide por conta própria.

# Padrão de Handoff entre Agentes (IA ↔ IA, IA ↔ Humano)

> **Referência:** Veuske/Rafa (2026-06-04)
> Use sempre que um cliente tem múltiplos agentes (ex: Vendas + SAC) ou handoff pra fila humana.

Padrão evoluído após bug de loop de transferência em produção. A v1 (agente seta `setor_agente` + dispara router genérico) é frágil. A v2 (flow dedicado por destino que JÁ seta o setor) é robusta.

---

## ⚠️ Leia primeiro: são DUAS camadas, e a regra é diferente em cada uma

Este documento trata da camada **IA ↔ IA**. Não confunda com o handoff para fila humana.

| | IA ↔ IA (qual AGENTE atende) | IA → fila humana (qual FILA recebe) |
|---|---|---|
| CUF | `setor_agente` | `motivo_transferencia` |
| Quem grava | **o flow dedicado** | **a IA** |
| Flows | **N dedicados**, 1 por destino | **UM** rotativo |
| Lido quando | Flow de Entrada, a CADA mensagem | uma vez, no disparo |
| Risco de loop | **sim** — o campo realimenta o roteamento | **não** — não volta para IA |

O antipadrão "1 router genérico por CUF" listado abaixo vale para a **primeira** coluna.
O bug do Veuske foi ali: `setor_agente` é relido a cada mensagem, então valor que não bate
com nenhum branch cai no default, e default apontando para uma IA fecha o ciclo.

Na segunda coluna esse vetor não existe — o rotativo entrega para gente, não para IA. Ali o
padrão canônico **é** um flow só filtrando o CUF, com duas condições obrigatórias:

1. O ramo `else` aponta para a **fila humana mais genérica** (SAC geral), nunca para uma IA.
2. A IA grava `motivo_transferencia` em TODA transferência — o campo persiste, e valor
   velho de um atendimento anterior manda a pessoa para a fila errada.

Enum canônico: `vendas` | `rastreio` | `devolucao` | `troca` | `duvidas` + `else` = SAC geral.
Ver `cufs_nextags.md` da skill `nextags-prompt-creator`.

---

## 🎯 Princípios

1. **1 flow dedicado por destino** — não tenta resolver tudo num só router
2. **Flow dispara o `set_field_value setor_agente`**, não o agente IA
3. **Agente IA só preenche contexto** (`resumo_pipeline`) e dispara o flow correto
4. **Case sensitivity** — UMA convenção (UPPERCASE ou lowercase) usada em TODOS os pontos
5. **`resumo_pipeline` viaja com a conversa** — próximo agente (humano ou IA) chega com contexto

---

## 🏗️ Arquitetura

```
Cliente → Flow de Entrada → lê setor_agente
                              ↓
                              ├─ NULL/vazio: set default (ex: PEDRO) → roteia
                              ├─ PEDRO: roteia pra agente Pedro
                              ├─ SOPHIA: roteia pra agente Sophia
                              └─ IGNORAR: roteia pra fila humana sem IA

Quando agente IA quer transferir:
  → set_field_value resumo_pipeline = "<contexto>"
  → send_flow <flow_dedicado_destino>

Flow dedicado (ex: 1781184556795 - "Transferir pra Sophia"):
  → set_field_value setor_agente = "SOPHIA"
  → send mensagem inicial pra Sophia (que lê {{resumo_pipeline}} e continua)
```

---

## 📊 CUF `setor_agente` — convenção

### Valores válidos (escolher 1 caso convention por cliente)

| Caso UPPERCASE (Veuske) | Caso lowercase |
|---|---|
| `PEDRO` (Vendas IA) | `pedro` ou `vendas` |
| `SOPHIA` (SAC IA) | `sophia` ou `sac` |
| `IGNORAR` (handoff humano completo) | `ignorar` ou `humano` |

**Regra crítica:** uma vez escolhido, NUNCA misturar. Audita todos os pontos:
- Flow de entrada (default e branches)
- Prompts dos agentes
- Flows dedicados de transferência
- Validators do CUF (se houver)
- Filtros de roteamento

Caso de falha real: Veuske tinha `setor_agente=PEDRO` no router mas o prompt do Pedro setava `humano`. Router não bateu → fallback PEDRO → loop infinito.

---

## 🔁 Tabela de flows dedicados (template pra novo cliente)

| Direção | Flow ID | O que faz |
|---|---|---|
| Qualquer → Vendas IA | `<FLOW_VENDAS_IA>` | seta `setor_agente=<VENDAS>` + msg inicial |
| Qualquer → SAC IA | `<FLOW_SAC_IA>` | seta `setor_agente=<SAC>` + msg inicial |
| Qualquer → SAC Humano | `<FLOW_SAC_HUMANO>` | atribui fila SAC humana, sem agente IA |
| Qualquer → Comercial Humano | `<FLOW_COMERCIAL_HUMANO>` | atribui fila Comercial humana, sem agente IA |

**Veuske (exemplo concreto):**

| Direção | Flow ID |
|---|---|
| → Sophia (SAC IA) | `1781184556795` |
| → Pedro (Vendas IA) | `1781184663034` |
| → SAC Humano | `1781184848081` |
| → Comercial Humano | `1781184926746` |

---

## 📝 CUF `resumo_pipeline` — contexto pra handoff

### Por que existe

Cliente conversa 10 turnos com Pedro. Em algum momento Pedro transfere pra Sophia. Sem `resumo_pipeline`:
- Sophia chega cega
- Sophia pergunta tudo de novo
- Cliente se frustra: "já contei isso pro Pedro..."

Com `resumo_pipeline` preenchido pelo Pedro antes de transferir:
- Sophia chega com contexto
- Primeira mensagem dela já é informada
- Cliente vê continuidade fluida

### Como preencher (regra pro prompt do agente)

Cada prompt deve instruir: "antes de qualquer transferência, gere 2-3 frases que cubram:
- Quem é o cliente (nome se souber)
- O que ele queria
- O que você já fez
- Por que está transferindo"

### Exemplos canônicos

✅ **Pedro → Sophia (pedido com problema durante venda):**
> "Leonir, cliente recorrente. Estava interessado em VK1000 + 1L Couro & Tabaco pra ambiente comercial 100m². Antes de finalizar, perguntou onde está o pedido #11488. Transfiro pra Sophia verificar."

✅ **Sophia → Pedro (cliente quer venda nova após resolver pedido):**
> "Leonir, cliente recorrente. Já tem VK1000 desde 2025. Veio pelo pós-venda mas demonstrou interesse em um VK200 pra segundo ambiente (escritório 80m² comercial). Não tem pedido pendente. Transfiro pro Pedro indicar."

✅ **Sophia → SAC Humano (caso jurídico):**
> "Leonir Nicaretta, pedido #11488 R$1538. Status 'Pago' há 12 dias sem despacho. Cliente quer cancelar e reembolso. Já está irritado."

❌ **Resumo ruim** ("vou transferir") — não dá contexto algum

### Onde Sophia/Pedro LÊEM o resumo

Na primeira mensagem ao receber o handoff, o agente referencia `{{resumo_pipeline}}` no prompt:

> "Você acabou de receber um cliente transferido. Leia `{{resumo_pipeline}}` pra entender o contexto e continue de onde o agente anterior parou. Não pergunte tudo de novo."

---

## ⚙️ Como configurar no NexTags

### 1. Flow de Entrada (executado em CADA mensagem)

```
[verifica setor_agente]
  ├─ vazio/NULL: set setor_agente = "<DEFAULT>" (ex: PEDRO) → roteia
  ├─ PEDRO: roteia pra agente Pedro
  ├─ SOPHIA: roteia pra agente Sophia
  ├─ IGNORAR: atribui fila humana, não chama IA
  └─ default (não bateu nada): atribui fila humana SAC (NUNCA define agente IA aqui)
```

⚠️ **NÃO inclua default = PEDRO** se o cliente fechar com `humano`. Default reset é causa do loop (Quirk #24).

### 2. Flows dedicados de transferência

Cada um faz EXATAMENTE 2 coisas:
1. `set_field_value setor_agente = "<DESTINO>"`
2. Envia 1 mensagem inicial pro destino continuar

Exemplo do flow `→ Sophia`:
```
Step 1: set_field_value setor_agente = "SOPHIA"
Step 2: send message {{first_name}} chegou aqui. Resumo: {{resumo_pipeline}}
        (essa mensagem inicia Sophia com contexto)
```

### 3. Validators (opcional, recomendado)

CUF `setor_agente` com validator:
- Tipo: string enum
- Valores aceitos: `PEDRO`, `SOPHIA`, `IGNORAR` (ou os 3 valores escolhidos)
- Rejeitar lowercase / case mismatch

Isso previne case errado entrar no campo e quebrar router.

---

## 🚫 Antipadrões — NUNCA fazer

| ❌ Errado | ✅ Certo |
|---|---|
| Agente seta `setor_agente` + dispara router genérico | Agente preenche `resumo_pipeline` + dispara flow dedicado por destino |
| 1 flow router que decide **qual AGENTE IA atende** baseado no CUF | N flows dedicados, 1 por destino |
| Confundir as camadas: usar `setor_agente` para escolher **fila humana** | Fila humana é `motivo_transferencia` + UM flow rotativo (ver bloco no topo) |
| Default do router = `PEDRO` (ou qualquer agente IA) | Default = fila humana (nunca volta pra IA por engano) |
| `setor_agente="humano"` em um prompt, `"IGNORAR"` em outro | Convenção única ratificada em TODOS os pontos |
| Agente IA continua tentando transferir após o flow não responder | Cláusula anti-loop: 2-3 tentativas, depois para e admite limitação |
| `resumo_pipeline` opcional / não obrigatório | Obrigatório em TODA transferência |

---

## ✅ Checklist de revisão de roteamento

- [ ] CUF `setor_agente` criado com validator de enum
- [ ] CUF `resumo_pipeline` criado (texto livre)
- [ ] Flow de Entrada com guard: só seta default se CUF está vazio
- [ ] Flow de Entrada default (não-match) → fila humana, NUNCA agente IA
- [ ] 1 flow dedicado por destino de AGENTE IA (não 1 router genérico)
- [ ] Handoff para fila HUMANA usa `motivo_transferencia` + 1 flow rotativo, com `else` numa fila humana
- [ ] Cada flow dedicado seta `setor_agente` E envia msg inicial
- [ ] Mensagem inicial referencia `{{resumo_pipeline}}` pro destino ler
- [ ] Prompts dos agentes:
  - [ ] Geram `resumo_pipeline` em 2-3 frases antes de transferir
  - [ ] NÃO setam `setor_agente` (deixam pro flow fazer)
  - [ ] Usam UMA convenção de case (PEDRO ou pedro, escolhida)
  - [ ] Cláusula anti-loop documentada
- [ ] Agente receptor (Sophia/Pedro) lê `{{resumo_pipeline}}` na primeira mensagem
- [ ] Teste fim-a-fim: handoff sem loop, contexto chegou

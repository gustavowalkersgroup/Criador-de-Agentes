# Padrão de Handoff — Roteamento de entrada e transferência para humano

> **Fonte de verdade do método:** `references/campos_canonicos.md` (cópia idêntica em
> `nextags-prompt-creator`, `nextags-prompt-fixer`, `nextags-mcp-builder` e
> `nextags-webhook-builder`). Este arquivo traduz o modelo canônico para o que a
> `nextags-mcp-builder` precisa saber para **construir** (ou auditar) o n8n por trás dele —
> nomes de node, ordem de steps, checklist de revisão. Para o enum completo, critérios de
> prioridade e regras de prompt, ver `campos_canonicos.md` §1-§3.
>
> **Escopo desta skill:** o MCP-builder **não decide** roteamento, enum nem prioridade —
> isso é do `nextags-prompt-creator`/`nextags-prompt-fixer`. O que cabe aqui é garantir que
> a infra (CUFs canônicos, tipo certo, Data Tables de apoio) exista para o modelo funcionar.

---

## 1. Diagrama do fluxo de entrada (canônico)

```
Início (toda mensagem)
  └─ 00 ROTEADOR — "Gerar texto" (modelo leve, temp 0), saída = 1 palavra
       grava setor_agente = vendas | sac | ignorar
       └─ Condição "setor_agente contém …":
            ├─ vendas → Agente Vendas → Filtro JSON (Executar código JS) → grava resposta_ia
            │                                                            → envia {{resposta_ia}}
            ├─ sac    → Agente SAC   → Filtro JSON                      → grava resposta_ia
            │                                                            → envia {{resposta_ia}}
            └─ else   → REVALIDADOR (1 palavra) grava tipo_setor = humano | bot
                          ├─ humano → volta pra condição de roteamento (atendimento normal)
                          └─ bot    → Arquivar conversa (tira da IA)
                                      → aguardar 1h (cancelado se o contato responder antes)
                                      → Bloquear contato
```

(evidência: fluxo de entrada em produção, screenshot 1 da rodada 2026-09; ver
`campos_canonicos.md` §1)

### Quem grava o quê — resumo pra quem constrói o n8n

| Node/passo | Grava | Nunca grava |
|---|---|---|
| **00 ROTEADOR** | `setor_agente` (única fonte) | `tipo_setor`, `motivo_transferencia` |
| **REVALIDADOR** (só no `else`) | `tipo_setor` | `setor_agente` |
| **Agente Vendas / SAC** (prompt) | `motivo_transferencia`, `prioridade_pipeline`, `resumo_pipeline` (antes de `send_flow`) | `setor_agente`, `tipo_setor`, `resposta_ia` |
| **Filtro JSON** (Executar código JS, 1 por agente) | `resposta_ia` | roteamento |
| **Fluxo de PIPELINE** (00-03) | `data_inicial_pipeline`, `Data_atual`, `data_vencimento`, tags de prioridade | `motivo_transferencia`/`prioridade_pipeline`/`resumo_pipeline` (esses são da IA) |

Tabela completa de todos os CUFs da conta modelo (inclui NPS, Instagram, disparo): ver
`campos_canonicos.md` §3. Tabela de etiquetas: §4.

⚠️ **Nenhuma IA transfere para outra IA.** O roteador é a ÚNICA coisa que roda a cada
mensagem e decide qual agente atende. Um agente que dispara um fluxo que muda
`setor_agente` para outro valor de IA reintroduz o loop do Quirk #27 (ver §5 abaixo) — se
você encontrar isso auditando um cliente existente, é bug, não feature.

---

## 2. Fluxo de pipeline — o que roda depois do `send_flow` de transferência

A IA, ao transferir para humano, grava o trio (`motivo_transferencia`,
`prioridade_pipeline`, `resumo_pipeline`) e dispara **UM** `flow_id` de pipeline — nunca um
por fila. Quem escolhe a fila é o VALOR do campo, não o `flow_id` (ver
`campos_canonicos.md` §2 pro JSON completo que a IA emite).

```
00 INÍCIO — grava data_inicial_pipeline = agora, Data_atual = agora,
            horario_atendimento = "Segunda a sexta-feira, das 8h às 18h" (texto do cliente)
01 SLA     — data_vencimento = agora + 2h (padrão; cliente pode mudar)
02         — Transferir conversa pra humano (tira da IA) + notifica operadores
03 ROTEADOR motivo_transferencia → painel:
   parcerias: ugc | colaboracao | influencer | revenda | atacado  → painel "Parcerias"
   comercial: vendas | carrinho                                    → painel "Comercial"
   sac:       rastreio | devolucao | troca | duvida                → painel "SAC"
   else (valor vazio/desconhecido)                                 → painel "SAC" (mesmo destino de duvida)
   Já existe card aberto? → SIM: comenta resumo_pipeline no card
                           → NÃO: cria card
   Lê prioridade_pipeline → seta prioridade do card (alta | media | else = baixa padrão)
   COMERCIAL → chama fluxo "Carteira Comercial"; SAC → Round Robin (fallback: admin fixo)
```

(evidência: fluxo de pipeline em produção, screenshot 2 da rodada 2026-09; detalhe completo
em `campos_canonicos.md` §2.0)

### Enum canônico de `motivo_transferencia` (pra construir o Switch do 03 ROTEADOR)

| Painel | Valores |
|---|---|
| Parcerias | `ugc`, `colaboracao`, `influencer`, `revenda`, `atacado` |
| Comercial | `vendas`, `carrinho` |
| SAC | `rastreio`, `devolucao`, `troca`, `duvida` (catch-all) |
| *(vazio/desconhecido)* | mesmo destino de `duvida` → painel SAC |

`prioridade_pipeline` é **Seleção única**: `baixa` \| `media` \| `alta`, `else = baixa`.
Critérios de quando usar cada valor: `campos_canonicos.md` §2.1 e §2.2. Extensão por
cliente (ex.: Cantarola usa `garantia` no painel de SAC) é permitida e registrada no
relatório — o valor extra cai em `duvida` a menos que o cliente peça o ramo dedicado
(evidência: documentos de projeto do cliente (Cantarola)).

---

## 3. Checklist de revisão de roteamento (auditoria de cliente ou setup novo)

- [ ] CUFs canônicos criados como tipo certo: `setor_agente` Texto, `tipo_setor` Seleção
      única, `motivo_transferencia` Texto, `prioridade_pipeline` Seleção única,
      `resumo_pipeline` Texto/Long Text (checklist completo: `campos_canonicos.md` §7.1)
- [ ] Existe **UM** roteador só, rodando a cada mensagem — não N flows dedicados por
      agente/destino
- [ ] Nenhum flow "troca de IA" — nenhum fluxo dispara `set_field_value setor_agente=<outra
      IA>` a partir de um agente. Só o roteador escreve `setor_agente`
- [ ] Revalidador só roda no `else`, só grava `tipo_setor`, nunca `setor_agente`
- [ ] `else` do fluxo de PIPELINE (motivo desconhecido/vazio) cai no painel **SAC**, mesmo
      destino de `duvida` — nunca cria painel novo nem descarta
- [ ] `else` de `prioridade_pipeline` (vazio/não reconhecido) = **baixa** — nunca alta por
      default
- [ ] `send_flow` do pipeline é sempre o ÚLTIMO item do array `actions`, depois dos 3
      `set_field_value` do trio
- [ ] Nenhum exemplo de `send_flow` de transferência no prompt sem o trio completo antes
      (campo STALE — ver `campos_canonicos.md` §2.4)
- [ ] Se o cliente tem `motivo_transferencia` fora do enum canônico, está registrado como
      exceção no relatório (não é bug — é extensão documentada)

---

## 4. Guard contra o loop do roteador (Quirk #27)

Auditando fluxo existente, confirme que:

1. O Flow de Entrada só define `setor_agente` default quando o campo está NULO/vazio —
   nunca sobrescreve um valor já setado por engano.
2. O ramo `humano` do roteador atribui fila humana e **para** — nunca reprocessa como se
   fosse valor de agente IA.
3. Case único (lowercase canônico) em todos os pontos: prompts, roteador, validators de
   CUF.

Detalhe técnico completo do bug e do fix: `references/quirks_n8n.md` Quirk #27.

---

## 5. Histórico: padrão Veuske (flows dedicados IA↔IA) e por que foi abandonado

O padrão anterior (Veuske/Rafa, 2026-06-04) resolvia "qual agente IA atende" com **N flows
dedicados, 1 por destino**: o agente gravava um resumo de contexto e disparava o flow de
destino, e **esse flow** gravava `setor_agente`. Foi abandonado porque `setor_agente` é
relido pelo fluxo de entrada a CADA mensagem: valor que não bate com nenhum branch cai no
default, e default apontando pra uma IA fecha o ciclo — loop infinito em produção (Pedro
respondeu 7+ vezes pra mesma mensagem, `setor_agente=PEDRO` no router resetando o `humano`
que o próprio Pedro tinha acabado de setar — Quirk #27).

O canônico substitui isso por **um roteador único** que roda a cada mensagem e é o ÚNICO
escritor de `setor_agente` (§1 acima): nenhuma IA transfere pra IA, some a classe inteira
de bug. A parte que **sobreviveu** do padrão Veuske foi o contexto de handoff — hoje é
`resumo_pipeline`, que deixou de viajar entre IAs e passou a ser o resumo que a IA escreve
antes de transferir pra HUMANO, indo direto pro card do pipeline (`campos_canonicos.md`
§2.3). Detalhe completo da migração: `campos_canonicos.md` §8.1.

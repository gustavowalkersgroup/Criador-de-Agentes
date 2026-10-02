# Relatório OctoberCut — {NOME_DO_AGENTE}

**Data:** {AAAA-MM-DD}
**Prompt:** {arquivo} ({tamanho antes} → {tamanho depois})
**Auditor:** `octobercut.py audit` — {N} bloqueios / {N} avisos antes → {N} / {N} depois

## Resumo

{2–4 linhas: o que mudou e a economia estimada.}

## Mensagens por cenário

| Cenário | Antes | Depois | Economia por atendimento |
|---|---|---|---|
| Abertura | {n} | {n} | R$ {x} |
| Diagnóstico / coleta | {n} | {n} | R$ {x} |
| Vitrine (por produto) | {n} | {n} | R$ {x} |
| Checkout | {n} | {n} | R$ {x} |
| Status de pedido | {n} | {n} | R$ {x} |
| Handoff | {n} | {n} | R$ {x} |

Custo por mensagem usado: R$ {rate} (confirmar no rate card vigente da Meta).
Estimativa a cada 1.000 atendimentos: R$ {antes} → R$ {depois} (−{pct}%).

## Alterações no prompt

| Seção | Antes | Depois | Regra OC |
|---|---|---|---|
| {seção} | {trecho/resumo} | {trecho/resumo} | OC-{n} |

## Preservado sem alteração

- Tom de voz e persona
- Regras de atendimento da marca
- `flow_id`s, CUFs e trio de handoff
- {outros}

## Pendências / validar em produção

- [ ] Conferir no WhatsApp real se o texto longo ficou legível (parágrafos).
- [ ] Conferir se o fluxo de handoff já envia mensagem (para tirar a transição da IA).
- [ ] Acompanhar o webhook `pricing.category = service` por 1–2 semanas e comparar com a estimativa.
- [ ] {outros}

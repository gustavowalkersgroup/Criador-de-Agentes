---
name: nextags-prompt-octobercut
description: "Adapta prompts de agentes NexTags (e o atendimento humano) à cobrança da Meta por mensagem de serviço, em vigor desde 01/10/2026: uma resposta = uma mensagem, sem typing 4 entre textos, abertura proativa, perguntas agrupadas, vitrine com 1 foto + 1 mensagem com botão, frase do link dentro do botão. Audita o .md do prompt ou o JSON de runtime, conta bolhas, funde mensagens e estima a economia. Use quando o usuário disser 'octobercut', 'cobrança da Meta', 'mensagem de serviço', 'reduzir mensagens', 'agrupar resposta', 'juntar balões', 'economizar WhatsApp', 'uma resposta uma mensagem', ou pedir para ajustar prompt/agente/skill à nova regra. Preserva tom de voz, persona, fluxos e regras de negócio."
---

# NexTags Prompt OctoberCut

Ajusta agentes de IA da NexTags (e orienta o atendimento humano) para a nova
cobrança da Meta: **desde 01/10/2026 toda mensagem não-template enviada pela
empresa é cobrada por mensagem** (categoria `service`), e as mensagens de
utilidade dentro da janela de 24h também. Cada bolha (balão) que o agente manda
gera uma cobrança. O objetivo desta skill é **diminuir o número de bolhas por
atendimento sem piorar a experiência**.

O detalhe da regra da Meta, com datas, tabela e valores, está em
`references/meta_pricing_out2026.md`. Leia quando precisar justificar uma
decisão ou calcular economia.

## Regra de ouro

> **Cada item de `messages` = 1 mensagem no WhatsApp = 1 cobrança.**
> O inteiro `4` (typing indicator) cria uma bolha nova, então gera outra
> cobrança. `\n` dentro de `text` quebra linha **na mesma bolha** e é de graça.

Mensagem do cliente não é cobrada. Só o que a empresa envia: texto da IA,
texto do atendente humano, imagem, botão, carrossel e mensagens que um fluxo
(`send_flow`) mande.

## As 8 regras OctoberCut (OC)

| # | Regra | Antes | Agora |
|---|---|---|---|
| OC-1 | **Uma resposta = uma mensagem.** O texto vai inteiro num só objeto `text`, com parágrafos via `\n\n`, até ~1.000 caracteres. Proibido typing `4` entre textos. | 4 bolhas no rastreio | 1 bolha |
| OC-2 | **Abertura proativa.** A primeira mensagem já diz como o agente ajuda, lista os caminhos e indica o próximo passo ("me manda seu CPF que eu já consulto"). | "Oi!" + "Como posso ajudar?" | 1 mensagem com os caminhos |
| OC-3 | **Conversa orientada por perguntas.** Quem atende conduz: perguntas fechadas ou com opções, pedindo **tudo o que precisa de uma vez** (CPF + nº do pedido, tipo de cabelo + objetivo). No máximo **uma rodada** de diagnóstico antes de indicar produto. | 1 pergunta por vez | perguntas agrupadas |
| OC-4 | **Não perguntar o nome por perguntar.** Usa `{{first_name}}` quando válido; se vazio/"Guest", saudação neutra, sem pedir nome. Só pede o nome se um processo exige, e junto com os outros dados. | "Qual seu nome?" | saudação neutra |
| OC-5 | **Vitrine enxuta.** Produto = **1 imagem + 1 button template** (descrição + preço + CTA + pergunta de follow-up no mesmo `text`). Fotos de variações só se a cliente pedir. | imagem + texto + botão + pergunta | imagem + botão |
| OC-6 | **Link de compra dentro do botão.** A frase ("Prontinho! Montei seu carrinho 💙") vai no `text` do button template, nunca numa bolha separada. | 2 mensagens | 1 mensagem |
| OC-7 | **Sem mensagem de espera.** Nada de "Deixa eu verificar…", "Um momento…": chama a tool e responde uma vez com o resultado. | 2 bolhas | 1 bolha |
| OC-8 | **Fechamento embutido.** "Qualquer coisa, tô por aqui" vai no fim da própria resposta. Sem mensagem só de despedida ou "posso ajudar em algo mais?" separada. Em handoff, se o fluxo de destino já fala com o cliente, `send_flow` vai sem `messages`. | bolha de despedida | frase no fim |

**O que NÃO muda:** tom de voz, persona, assinatura de abertura, regras de
atendimento da marca, base de conhecimento, `flow_id`s, CUFs, trio de handoff
(`motivo_transferencia` + `prioridade_pipeline` + `resumo_pipeline`) e todas
as Regras Absolutas das outras skills NexTags.

### Limites técnicos que embasam o "~1.000 caracteres"

- `text` do **button template** vira o *body* de mensagem interativa do
  WhatsApp: **máximo 1.024 caracteres**. Acima disso, a Meta rejeita.
- Texto simples aceita até 4.096, mas acima de ~1.000 fica cansativo no
  celular. Mire **300–900**; passou de 1.000, enxugue antes de quebrar.
- Título de botão continua **≤ 20 caracteres** (regra 24 das Regras Absolutas).
- Carrossel `generic` (≥ 2 cards) é **1 item** em `messages`, mas a
  renderização no WhatsApp depende do canal: valide no celular antes de usar
  como "vitrine de 1 mensagem".

## Fluxo de trabalho

### Modo A — Ajustar um prompt existente (`.md`)

1. Salve o prompt e rode o auditor:
   ```bash
   python <SKILL_DIR>/scripts/octobercut.py audit <prompt.md> --report /tmp/oc_findings.json
   ```
   Ele extrai os exemplos JSON do prompt, conta bolhas por exemplo e varre a
   prosa atrás de instruções que multiplicam mensagens ("separados por typing
   4", "3 blocos", "pergunte o nome", "uma pergunta por vez", "deixa eu
   verificar"…).
2. Reescreva o prompt seguindo `references/guia_reescrita.md`:
   - insira o bloco canônico de `references/bloco_octobercut.md` logo depois
     da seção de formato JSON;
   - reescreva cada exemplo JSON para o formato de 1 mensagem (veja
     `references/padroes_antes_depois.md`);
   - ajuste abertura, framework de conversa, vitrine, checkout, handoff e
     encerramento;
   - remova ou neutralize as instruções antigas que pediam várias bolhas.
     **Instrução contraditória é pior que nenhuma:** se sobrar "use 3 blocos
     separados por typing 4" em algum canto, o LLM obedece.
3. Rode o auditor de novo até zerar os bloqueios. Depois rode o
   `nextags-prompt-fixer` (ou o `analyze_prompt.py` dele) para garantir que
   nenhuma Regra Absoluta quebrou.
4. Entregue: prompt `.md` ajustado + relatório no formato de
   `assets/relatorio_template.md` (bolhas antes/depois por cenário e
   estimativa de economia).

### Modo B — Auditar ou fundir o JSON de runtime

Quando o usuário cola respostas reais do bot:

```bash
python <SKILL_DIR>/scripts/octobercut.py merge <saida.json> --output /tmp/merged.json
```

O `merge` remove typing `4`, junta textos consecutivos com `\n\n`, embute
texto vizinho no `text` do button template (se couber em 1.024) e passa o
texto que vinha antes de uma imagem para a mensagem seguinte. Ele **não
inventa conteúdo** nem remove imagens. Use o resultado como exemplo de
"depois" ao reescrever o prompt; o conserto definitivo é sempre no prompt.

### Modo C — Estimar a economia

```bash
python <SKILL_DIR>/scripts/octobercut.py estimate --before 7 --after 2 --rate 0.035 --volume 1000
```

`--rate` é o custo por mensagem em R$. O padrão 0,035 é o que se deduz das
estimativas internas (R$ 0,25 por 7 mensagens). A Meta revisa o rate card
até trimestralmente, então confirme o valor vigente antes de apresentar o
número a um cliente.

### Modo D — Atendimento humano

O atendente humano também gera mensagem de serviço cobrada. Quando o pedido
envolver o time (treinamento, macro, script de atendimento), use
`assets/guia_atendente_humano.md`.

## Integração com as outras skills NexTags

Desde a versão 1.9.0 as skills irmãs já seguem o OctoberCut:

| Skill | O que faz com o OctoberCut |
|---|---|
| `nextags-prompt-creator` | Bloco OctoberCut obrigatório no `prompt_skeleton.md` (§6), exemplos em 1 mensagem, vitrine enxuta (§6B.5), abertura proativa e diagnóstico em 1 rodada; bateria de teste com contagem de bolhas. |
| `nextags-prompt-fixer` | Regra 28 em `regras_absolutas.md`; o `analyze_prompt.py` avisa `octobercut_bolhas`, `octobercut_instrucao` e seção `formato_economico_octobercut` ausente (warn; `text` de botão >1024 é block). |
| `nextags-json-fixer` | Não altera o JSON (typing `4` segue válido), mas o relatório traz `octobercut_warnings` com a contagem de bolhas. |
| `nextags-webchat-tester` | Mostra `[OctoberCut] N bolha(s)` por turno e avisa acima de 1 (texto) ou 2 (produto). |
| `nextags-webhook-builder` / `nextags-mcp-builder` | Notas de custo: fluxo manda 1 mensagem completa por evento; tool devolve tudo numa chamada. |

Se encontrar uma cópia antiga dessas skills (instalação desatualizada) que ainda
mande "3 blocos separados por typing 4" ou "pergunte o nome UMA vez", o OctoberCut
vence. Para realinhar uma cópia antiga, use `prompts/ajustar-skills-octobercut.md`
na raiz do repo. O schema JSON **não muda**: typing `4` continua sintaticamente
válido; é regra de custo, aplicada no prompt.

## O que esta skill NÃO faz

- Não altera persona, tom, regras de negócio, preços, `flow_id`s ou CUFs.
- Não corrige JSON quebrado (isso é da `nextags-json-fixer`) nem audita as
  Regras Absolutas (isso é da `nextags-prompt-fixer`).
- Não decide a categoria de cobrança de templates (marketing/utilidade):
  isso é dos fluxos e disparos (`nextags-webhook-builder`).
- Não promete economia exata: os números são estimativas até medir nas
  conversas reais.

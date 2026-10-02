# Prompt: alinhar as skills NexTags ao OctoberCut

Cole o texto abaixo (da linha `---` em diante) numa sessão do Claude Code ou do
Codex aberta na raiz do repositório `Criador-de-Agentes`. Ele adapta as skills
existentes à cobrança da Meta por mensagem de serviço sem quebrar o que já
funciona.

---

Você vai alinhar as skills deste repositório à regra **OctoberCut**: desde
01/10/2026 a Meta cobra cada mensagem não-template que a empresa envia no
WhatsApp (categoria `service`, IA de terceiros ou humano). Cada item do array
`messages` é uma mensagem cobrada, e o typing indicator inteiro `4` cria uma
bolha nova (outra cobrança).

**Fonte da verdade:** `skills/nextags-prompt-octobercut/` (leia `SKILL.md`,
`references/bloco_octobercut.md`, `references/padroes_antes_depois.md` e
`references/guia_reescrita.md` antes de começar). As 8 regras OC-1 a OC-8
estão no `SKILL.md`.

**Não mude:** o schema JSON da plataforma (typing `4` continua sintaticamente
válido), persona/tom, Regras Absolutas existentes, campos canônicos, trio de
handoff, `flow_id`s, inventário Walkers. A mudança é de **boa prática de
custo**, não de validade do JSON.

## Tarefas

### 1. `skills/nextags-prompt-creator`

- `references/prompt_skeleton.md`:
  - Inserir o bloco de `bloco_octobercut.md` logo depois da seção de formato
    JSON e marcá-lo como obrigatório em todo prompt gerado.
  - Reescrever **todos** os exemplos JSON para o padrão de 1 mensagem: tirar
    o exemplo "Resposta com pausa natural (separador 4…)"; vitrine vira
    imagem + 1 button template com descrição, preço e pergunta no `text`;
    link de compra com a frase dentro do botão.
  - §6B.5: trocar "3 blocos separados por typing 4" e "NUNCA misture texto com
    mídia/link no mesmo bloco" pela vitrine enxuta (OC-5/OC-6). Fotos de
    variações só se o cliente pedir.
  - §6B.1/§6B.2: abertura proativa na mesma bolha da assinatura (OC-2);
    diagnóstico com no máximo uma rodada de perguntas agrupadas (OC-3).
  - §1.7.1 e todo "pergunte o nome UMA vez": trocar por saudação neutra sem
    pedir nome; só pedir quando um processo exige, junto com outros dados
    (OC-4).
  - Notas sobre `4` vs `\n`: manter a explicação técnica, mas dizer que o `4`
    não deve ser usado por custo.
- `references/prompt_template.md` e `references/arquitetura_suprema_v7.md`:
  trocar "uma pergunta (relevante) por vez" por "uma rodada de perguntas
  agrupadas"; trocar o pedido de nome como acima.
- `references/cufs_nextags.md` (linha do `{{first_name}}`): ajustar a regra de
  nome inválido para "saudação neutra, não perguntar".
- `references/auditoria_tom_e_claims.md`: incluir no checklist "resposta em
  uma bolha", "sem mensagem de espera" e "fechamento embutido".
- `assets/stress_test_battery_template.md`: adicionar casos que contam bolhas
  (abertura, vitrine, checkout, rastreio, handoff) com o máximo esperado:
  1 bolha por resposta de texto, 2 por produto (imagem + botão).
- `assets/relatorio_template.md`: adicionar a seção "Mensagens por cenário"
  (copiar de `nextags-prompt-octobercut/assets/relatorio_template.md`).
- `SKILL.md`: incluir o OctoberCut entre os passos obrigatórios de geração e
  mandar rodar `python <octobercut>/scripts/octobercut.py audit` no prompt
  gerado, junto do `analyze_prompt.py`.
- `scripts/analyze_prompt.py`: adicionar checks de severidade **warn** (não
  block, para não quebrar prompts antigos de uma vez) para typing `4` em
  exemplos, ausência do bloco "FORMATO ECONÔMICO DE RESPOSTA (OCTOBERCUT)" e
  instruções "separados por typing 4" / "pergunte o nome". Pode importar a
  lógica do `octobercut.py` ou reimplementar o mínimo. Atualizar
  `test_analyze_prompt.py` e `test_v7_contract.py` se algum teste depender dos
  exemplos antigos.

### 2. `skills/nextags-prompt-fixer`

- `references/regras_absolutas.md`: nova regra "Agrupamento de mensagens
  (OctoberCut)" com Regra / Why (cobrança por mensagem) / How to apply,
  severidade **warn**.
- `SKILL.md`: incluir a regra na tabela de correções: fundir textos com
  typing `4`, levar frase para dentro do button template, remover mensagem de
  espera, inserir o bloco OctoberCut se faltar.
- `scripts/analyze_prompt.py`: os mesmos checks da tarefa 1 (as duas cópias
  do analisador devem ficar consistentes; conferir com `diff`).
- `references/campos_canonicos.md` e `references/cufs_nextags.md`: manter
  idênticos às cópias do prompt-creator (rodar `diff` entre as cópias no fim).

### 3. `skills/nextags-json-fixer`

- `references/schema.md`: na seção de typing indicator, acrescentar nota de
  custo: válido no schema, mas cada bolha é cobrada; o fixer **não** remove
  `4` por conta própria.
- `scripts/fix_json.py`: incluir no relatório um **aviso** (não correção)
  com a contagem de bolhas e a sugestão de rodar `octobercut.py merge` quando
  houver typing `4` ou textos consecutivos. Atualizar `test_fix_json.py`.

### 4. `skills/nextags-webchat-tester`

- Registrar no relatório de cada turno quantas bolhas o agente mandou e
  marcar aviso quando passar de 1 (texto) ou 2 (produto).

### 5. `skills/nextags-webhook-builder` e `skills/nextags-mcp-builder`

- Só documentação: mensagens de fluxo (`send_flow`) também são cobradas.
  Lembrar que fluxos de handoff/transacionais devem mandar o mínimo de
  mensagens e que mensagem de utilidade dentro da janela de 24h passou a ser
  cobrada. Não alterar código.

### 6. Fechamento

- Rodar todos os testes: `python skills/*/scripts/test_*.py` (de dentro de
  cada pasta `scripts`).
- Rodar `python skills/nextags-prompt-octobercut/scripts/octobercut.py audit
  skills/nextags-prompt-creator/references/prompt_skeleton.md` e chegar a 0
  bloqueios.
- Atualizar `CHANGELOG.md` (nova versão minor), versões em
  `.claude-plugin/plugin.json` e `.claude-plugin/marketplace.json`, e
  regenerar os zips com `bash scripts/build_dist.sh`.
- Entregar um resumo em PT-BR: arquivos alterados, o que mudou em cada skill,
  testes rodados e qualquer ponto que precise de decisão humana.

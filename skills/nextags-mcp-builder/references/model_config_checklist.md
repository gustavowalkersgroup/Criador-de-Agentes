# Checklist de Config de Modelo — Agente NexTags com Tools

> **Referência:** Veuske/Pedro 2026-06-11
> Use sempre que terminar de plugar MCP em um agente NexTags. Config errada de modelo anula horas de prompt engineering.

> ⚠️ **Temperatura não existe mais no painel (confirmado pelo dono, 26/10/2026).** O agente usa o padrão do provedor (~0,98) e a tela só mostra **Max tokens**, **Reasoning effort** e o **Tipo de resposta da IA** (Verbosity aparece conforme o modelo). A página `help.nextags.com.br/tutoriais/ia/modelo-e-parametros` ainda cita temperatura 0–2: está desatualizada. As menções a temperatura abaixo são do caso Veuske (jun/2026), quando o ajuste ainda existia.

## 🎯 Config canônica recomendada

| Setting | Valor | Por quê |
|---|---|---|
| **Modelo** | Claude Sonnet 4.6 (ideal) **OU** GPT 5.4 não-mini | "Mini" perde adesão em prompts longos (>500 linhas). Sonnet 4.6 e GPT 5.4 (não-mini) seguem instruções de forma confiável e fazem tool calling robusto. A lista de modelos vem do provedor e muda com o tempo: confira o nome exato no painel. |
| **Reasoning effort** | Alta (opções: Nenhum/Baixa/Média/Alta; padrão Baixa) | Permite o modelo "pensar" antes de decidir entre tool e texto. Compatível com Sonnet/GPT 5.4. O ajuste só aparece nos modelos que o aceitam. |
| **Verbosity** | Média | Baixa demais empurra modelo a responder rápido sem chamar tool. Alta gasta token à toa. |
| **Max tokens** | Alto (1–32768; padrão 2048) | Tool calling consome tokens (raciocínio + chamada + processar resposta). Curto demais corta no meio. |

Onde fica: ícone de ajustes à direita de **Mensagem do sistema**, no editor do agente; clique em **Salvar** depois de mudar. Mude uma coisa de cada vez e teste. Pela API, `POST /agents/{id}` aceita `model` e `max_output_tokens`, mas **não use**: um POST com esses campos travou o painel em 23/10/2026 (ver skill `nextags-api`); configure no painel.

Referência da skill oficial da NexTags (`guiipego/nextags`, 26/10/2026), para agente **sem** MCP: GPT-6 Luna, Max tokens 32768, Reasoning effort Média, Verbosity Baixa. Com tools mantemos Reasoning alta e Verbosity média (caso Veuske); confirme no teste fim-a-fim.

## 🚨 Armadilha clássica — NUNCA use

| Setting hostil | O que acontece | Veuske observou |
|---|---|---|
| Modelo mini com prompt >500 linhas | Modelo "esquece" instrução do meio do prompt | Pedro pulou `buscar_produto_veuske` mesmo com 24 menções explícitas |
| Modelo mini com Reasoning/Verbosity baixos (no caso Veuske de jun/2026 somava-se temperature alta, ajuste que não existe mais no painel) | Modelo parafraseia respostas, pula tool, inventa dado | Pedro gerou 7 variações da mesma frase ("Vou confirmar com o time...") no mesmo loop |
| Verbosity baixa + reasoning alta + mini | Reasoning ocupa contexto sem ter capacidade de processar → ações erradas | Pedro inventou handle `vk1000` (sem hífen) em vez de buscar |

## 🩺 Sintomas que indicam config errada de modelo

Se você ver **qualquer** desses comportamentos depois de plugar o MCP, **revise config de modelo ANTES de mexer no prompt**:

- ✗ Agente "diz que vai chamar" mas não chama a tool
- ✗ Mesma resposta com palavras diferentes a cada turno ("Vou confirmar...", "Perfeito, vou direcionar...", "Vou verificar com o time...")
- ✗ Agente inventa dado (handle, ID, preço) em vez de consultar
- ✗ Loop de transferência (combinado com Quirk #27)
- ✗ Resposta inconsistente (ora tool, ora texto criativo, ora transferência)
- ✗ Agente ignora regras explícitas do prompt mesmo com proibição inegociável

Esses sintomas formam a **assinatura clássica de modelo pequeno com pouco raciocínio** (no caso Veuske, de jun/2026, somava-se temperature alta, que hoje não é ajustável). Não é prompt, não é MCP — é o motor.

## ✅ Checklist pra rodar com o user no final do setup

Antes de marcar projeto como entregue:

- [ ] Modelo é Sonnet 4.6 ou GPT 5.4 não-mini?
- [ ] Verbosity média ou alta?
- [ ] Reasoning effort alta (se modelo suporta)?
- [ ] Max tokens alto (até 32768)?
- [ ] Teste fim-a-fim: cliente pediu produto → agente chamou tool → recebeu link com handle real?

## 📋 Exemplo de mensagem pro user no fim do setup

```
Setup MCP completo. Antes de testar com cliente real, confirma a config do modelo do agente no painel NexTags:

✅ Modelo: Claude Sonnet 4.6 (ou GPT 5.4 não-mini)
✅ Reasoning: alta
✅ Verbosity: média
✅ Max tokens: alto

Se algum desses estiver diferente — especialmente modelo "mini" — o agente vai pular tools e inventar dado. Vi isso na Veuske (jun/2026, quando o painel ainda tinha temperatura): temperature 8 + GPT mini = Pedro mandou cliente pra 404 e travou em loop. Mudou pra temp 2 + Sonnet 4.6 → funcionou no primeiro teste.
```

## 🔗 Cross-references

- `references/quirks_n8n.md` Quirk #27 — loop de transferência pode ter config de modelo como **co-fator** (não só flow). Verifique os 2.
- `references/handoff_pattern.md` — roteador único/revalidador certos sozinhos não consertam se o modelo tá inventando.
- `references/tool_descriptions_guide.md` — descrição perfeita não compensa modelo mini com pouco raciocínio.

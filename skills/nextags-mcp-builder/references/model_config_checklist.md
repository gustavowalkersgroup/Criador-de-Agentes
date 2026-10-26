# Checklist de Config de Modelo — Agente NexTags com Tools

> **Referência:** Veuske/Pedro 2026-06-11
> Use sempre que terminar de plugar MCP em um agente NexTags. Config errada de modelo anula horas de prompt engineering.

> ⚠️ **Escala da temperatura (doc oficial, 25/10/2026):** a tela atual do agente vai de **0 a 2**, padrão **0,4**, e a doc recomenda valores baixos para atendimento (`help.nextags.com.br/tutoriais/ia/modelo-e-parametros`). Os números de temperatura deste checklist ("2", "≤ 3", "≥ 6", "8") são da época da Veuske (jun/2026) numa escala **0–10** [Provável]. Na faixa 0–2 de hoje, **2 é o máximo**: o oposto do que o checklist quer. **Confira a escala no painel antes de aplicar.** Se for 0–2, use o padrão 0,4; acima de ~1,2 (equivalente proporcional ao "≥ 6") trate como zona de risco [Especulação: a conversão proporcional não consta na doc].

## 🎯 Config canônica recomendada

| Setting | Valor | Por quê |
|---|---|---|
| **Modelo** | Claude Sonnet 4.6 (ideal) **OU** GPT 5.4 não-mini | "Mini" perde adesão em prompts longos (>500 linhas). Sonnet 4.6 e GPT 5.4 (não-mini) seguem instruções de forma confiável e fazem tool calling robusto. A lista de modelos vem do provedor e muda com o tempo: confira o nome exato no painel. |
| **Temperature** | **Baixa**: 0,4 na escala 0–2 de hoje (era "2" na escala 0–10 da época) | Tool calling exige determinismo. Temperature alta = modelo "criativo" pula tool, inventa dado, parafraseia indefinidamente. |
| **Reasoning effort** | Alta (opções: Nenhum/Baixa/Média/Alta; padrão Baixa) | Permite o modelo "pensar" antes de decidir entre tool e texto. Compatível com Sonnet/GPT 5.4. O ajuste só aparece nos modelos que o aceitam. |
| **Verbosity** | Média | Baixa demais empurra modelo a responder rápido sem chamar tool. Alta gasta token à toa. |
| **Max tokens** | Alto (1–32768; padrão 2048) | Tool calling consome tokens (raciocínio + chamada + processar resposta). Curto demais corta no meio. |

Onde fica: ícone de ajustes à direita de **Mensagem do sistema**, no editor do agente; clique em **Salvar** depois de mudar. Mude uma coisa de cada vez e teste. Pela API, `POST /agents/{id}` aceita `model` e `max_output_tokens`, mas **não use**: um POST com esses campos travou o painel em 23/10/2026 (ver skill `nextags-api`); configure no painel.

## 🚨 Armadilha clássica — NUNCA use

| Setting hostil | O que acontece | Veuske observou |
|---|---|---|
| Modelo mini com prompt >500 linhas | Modelo "esquece" instrução do meio do prompt | Pedro pulou `buscar_produto_veuske` mesmo com 24 menções explícitas |
| Temperature alta (≥ 6 na escala 0-10 da época; ≳ 1,2 na 0–2 atual [Especulação]) | Modelo parafraseia respostas, pula tool, inventa dado | Pedro gerou 7 variações da mesma frase ("Vou confirmar com o time...") no mesmo loop |
| Verbosity baixa + reasoning alta + mini | Reasoning ocupa contexto sem ter capacidade de processar → ações erradas | Pedro inventou handle `vk1000` (sem hífen) em vez de buscar |

## 🩺 Sintomas que indicam config errada de modelo

Se você ver **qualquer** desses comportamentos depois de plugar o MCP, **revise config de modelo ANTES de mexer no prompt**:

- ✗ Agente "diz que vai chamar" mas não chama a tool
- ✗ Mesma resposta com palavras diferentes a cada turno ("Vou confirmar...", "Perfeito, vou direcionar...", "Vou verificar com o time...")
- ✗ Agente inventa dado (handle, ID, preço) em vez de consultar
- ✗ Loop de transferência (combinado com Quirk #27)
- ✗ Resposta inconsistente (ora tool, ora texto criativo, ora transferência)
- ✗ Agente ignora regras explícitas do prompt mesmo com proibição inegociável

Esses sintomas formam **assinatura clássica de temperature alta em modelo pequeno**. Não é prompt, não é MCP — é o motor.

## ✅ Checklist pra rodar com o user no final do setup

Antes de marcar projeto como entregue:

- [ ] Modelo é Sonnet 4.6 ou GPT 5.4 não-mini?
- [ ] Temperatura baixa (0,4 na escala 0–2; ≤ 3 se a tela ainda for 0–10)?
- [ ] Verbosity média ou alta?
- [ ] Reasoning effort alta (se modelo suporta)?
- [ ] Max tokens alto (até 32768)?
- [ ] Teste fim-a-fim: cliente pediu produto → agente chamou tool → recebeu link com handle real?

## 📋 Exemplo de mensagem pro user no fim do setup

```
Setup MCP completo. Antes de testar com cliente real, confirma a config do modelo do agente no painel NexTags:

✅ Modelo: Claude Sonnet 4.6 (ou GPT 5.4 não-mini)
✅ Temperatura: baixa (0,4 na escala 0–2; confira a escala da tela)
✅ Reasoning: alta
✅ Verbosity: média
✅ Max tokens: alto

Se algum desses estiver diferente — especialmente temperatura alta ou modelo "mini" — o agente vai pular tools e inventar dado. Vi isso na Veuske: temperature 8 + GPT mini = Pedro mandou cliente pra 404 e travou em loop. Mudou pra temp 2 + Sonnet 4.6 → funcionou no primeiro teste.
```

## 🔗 Cross-references

- `references/quirks_n8n.md` Quirk #27 — loop de transferência pode ter config de modelo como **co-fator** (não só flow). Verifique os 2.
- `references/handoff_pattern.md` — roteador único/revalidador certos sozinhos não consertam se o modelo tá inventando.
- `references/tool_descriptions_guide.md` — descrição perfeita não compensa modelo mini com temperature 8.

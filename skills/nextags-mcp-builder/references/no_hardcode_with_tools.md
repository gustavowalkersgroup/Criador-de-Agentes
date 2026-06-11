# 🔒 Regra de ouro — NUNCA hardcode no prompt o dado que a tool retorna

> **Referência:** Veuske/Pedro 2026-06-11
> A causa #1 de "o agente não usa a tool" não é config nem MCP quebrado — é **dado duplicado entre prompt e tool**.

## O problema

Quando o agente tem uma tool (MCP) que retorna um dado E o mesmo dado está escrito no prompt, o modelo **recita o prompt em vez de chamar a tool**. Isso é racional do ponto de vista do modelo: por que fazer um tool call (lento) pra buscar algo que já está no contexto dele?

Sintomas idênticos a "modelo não usa tool":
- Agente cita preço/estoque/fragrância de memória (desatualizado)
- Agente inventa handle/URL (404 no cliente)
- Agente nunca chama a tool, mesmo com regras explícitas "SEMPRE chame a tool"
- Config (modelo, temperature) e MCP estão perfeitos — não é isso

## Caso Veuske (evidência forense)

O prompt do Pedro tinha:
- Tabela de preços completa (VK50 R$649 ... VK1000 R$4950) com ranges de m²
- Listas de fragrâncias ("Bamboo · Chá Branco · Lavanda · +150...")
- Preços de kit/refil/tester

E ao mesmo tempo a tool `buscar_produto_veuske`. Resultado:
- Pedro recitava preço/fragrância de memória
- Inventava handle (mandou `vk1000` sem hífen → 404; o real é `vk-1000`)
- **Execuções do n8n = 0** durante os testes → confirmado que NÃO chamava a tool

Removido o catálogo do prompt → Pedro passou a chamar a tool e mandar link real com handle correto. Cliente confirmou: *"MCP + hardcode dá problema"*.

Detalhe fino: até lista PARCIAL hardcoded envenena. Mantivemos as "famílias olfativas" (cítrico/amadeirado/floral) como guia de conversa → o agente recitava as famílias em vez de chamar `listar_fragrancias_veuske`. **Hardcode zero quando existe tool pra aquilo.**

## A regra

| ❌ NÃO colocar no prompt (a tool retorna) | ✅ PODE ficar no prompt |
|---|---|
| Preços | Lógica de venda: qual modelo pra qual ambiente (SEM preço) |
| Catálogo de produtos / SKUs | Políticas de marca: frete, garantia, formas de pagamento |
| Nomes de fragrâncias / sabores / cores | Persona, tom de voz, regras de atendimento |
| Estoque / disponibilidade | Fluxos de transferência, gatilhos de SAC |
| Handles / URLs de produto | Diferenciais da marca (claims gerais, não SKU) |
| Specs que mudam (capacidade, dimensões) | Como CONSTRUIR o link (template com {handle} da tool) |

## Como aplicar (mcp-builder)

Quando esta skill cria tools que retornam catálogo/preço/estoque, **avise o autor do prompt** (nextags-prompt-creator) no relatório de entrega:

```
⚠️ As tools <X, Y> retornam preço, catálogo e fragrâncias dinamicamente.
NÃO hardcode esses dados no prompt do agente — senão o modelo recita o
hardcode e ignora a tool (caso Veuske 2026-06-11). No prompt, mantenha só
lógica de venda e persona; preço/produto/fragrância sempre via tool.
```

Adicione ao prompt do agente um banner:

```
🔒 Este prompt NÃO tem catálogo. Preço, fragrância, estoque e handle vêm
SÓ da tool. Qualquer dado que você ache que lembra está DESATUALIZADO.
```

## Segundo aprendizado do mesmo caso — OBJETIVO numerado vicia o modelo

O prompt do Pedro tinha OBJETIVO em lista numerada: "1. entender ambiente ... 6. enviar link". O modelo seguia a ordem LITERAL — qualificava sempre primeiro, link só no fim. Cliente pedia link direto e ele qualificava/escalava.

Fix: **2 modos explícitos.**
- **Modo A** — cliente já sabe (nomeou produto OU pediu link/preço) → busca na tool e ENTREGA, sem re-qualificar.
- **Modo B** — cliente não sabe → consultivo (qualifica ambiente → recomenda → busca → fecha).

E um **REFLEXO Nº 1** no topo do prompt: "produto mencionado → 1ª ação é chamar a tool, antes de escrever texto. Transferir/escalar sem ter buscado é o erro mais grave."

## Cross-references

- `references/model_config_checklist.md` — quando config É o problema (mini + temp alta). Aqui NÃO era — descartar config antes de culpar.
- `references/link_envio_pattern.md` — anti-alucinação de handle (mesma raiz: dado no prompt vence a tool).
- `references/quirks_n8n.md` — busca Shopify casa por token inteiro: "VKLUXE" acha, "vk luxe" (espaço) e "Luxe" (substring) dão 0. Instrua o agente a colar código sem espaço e buscar fragrância por palavra distintiva.

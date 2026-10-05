# Lições do caso e-commerce de acessórios pet (05/10/2026)

| # | O que aconteceu | Causa | Solução |
|---|---|---|---|
| 1 | Resposta pública sem @ | O modelo não tinha o username | Bloco "DADOS DESTE COMENTÁRIO" com `{{ig_user_name}}` e `{{username}}` |
| 2 | Comentário de preço virou `IGNORAR` | Regra de segurança para autor inválido | Autor inválido responde sem @. `IGNORAR` só para spam/ofensa |
| 3 | DM perguntou "como posso te chamar" | Prompt de vendas não usava `first_name` | Regra: nome vem de `{{first_name}}`, nunca perguntar |
| 4 | `(#100) The parameter recipient is required` | Falha transitória do Instagram/NexTags (passou sozinho) | Reteste; não é do prompt |
| 5 | JSON `messages: []` colado na resposta fixa não gerou DM | Passo de DM do Instagram não interpreta JSON | Decisão por campo `decisao_dm` + agente classificador com `send_flow` |
| 6 | Preço divergente entre a resposta da equipe e o site | Preço humano vs tabela | Preço sempre do MCP, "a partir de" |
| 7 | Promoção vencida citada | Prompt com campanha fixa | Variável `campanha_ativa` (não por padrão) |
| 8 | Resposta pública muito repetitiva | Mesmas expressões ("né", "bom gosto") | Regra de variar; sem repetir em respostas seguidas |

## Padrão de respostas da equipe (para calibrar tom em novos clientes)
- Inicia com `@usuario`, 1 linha, informal e afetuosa, 1 a 2 emojis.
- Preço: "a partir de R$X" + contexto + "vou te mandar o link no direct". Nunca cola link no comentário.
- Frete grátis: sempre as duas regras numa frase.
- Humor leve em post de meme; nunca em reclamação/preço.
- Reconhece cliente recorrente pelo nome do pet.

## Números da amostra (referência)
~330 comentários, ~4% perguntas reais; metade é preço/link. ~10% de gatilho para DM; o classificador deve dar `NAO` na grande maioria.

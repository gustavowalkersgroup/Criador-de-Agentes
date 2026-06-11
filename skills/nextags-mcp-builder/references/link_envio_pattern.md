# Padrão de Envio de Link com UTM — TODOS os clientes

> **Princípio universal:** qualquer link enviado pelo agente ao cliente DEVE carregar `?utm_source=whatsapp&utm_medium=<agente>&utm_campaign=<campanha>`.
>
> Aplicar a TODOS os clientes (Shopify, Yampi, Tray, VTEX, Nuvemshop, Bling, Martz, etc.), em TODOS os contextos onde o agente envia link de produto, kit, catálogo, checkout, ou qualquer página da loja.

---

## 🎯 Por que UTM é INEGOCIÁVEL

Sem UTM:
- ❌ Lojista não consegue saber se a venda veio do WhatsApp ou de outra fonte
- ❌ Não dá pra mensurar ROI do agente IA
- ❌ Atribuição perdida em todas as ferramentas de analytics (Shopify Reports, GA4, Meta Ads, etc.)
- ❌ Cliente paga investimento em IA mas não consegue justificar via dados

Com UTM:
- ✅ Dashboard de Vendas do Shopify/loja mostra exatamente quantas vendas vieram do agente
- ✅ GA4 separa fonte/canal/campanha
- ✅ ROI calculável: "Pedro fechou R$ X em vendas no último mês"
- ✅ A/B test possível: testa 2 campanhas (`indicacao_consultiva` vs `recuperacao_carrinho`) e mede qual converte mais

---

## 🏷️ Padrão UTM oficial

```
?utm_source=whatsapp&utm_medium=<nome_do_agente>&utm_campaign=<contexto_envio>
```

### Parâmetros por dimensão

| Parâmetro | Valor | Significado |
|---|---|---|
| `utm_source` | `whatsapp` (fixo) | Canal de origem do tráfego — sempre WhatsApp em integrações NexTags |
| `utm_medium` | `<agente_origem>` | Qual agente mandou o link. Ex: `pedro_vendas`, `sophia_sac`, `luna_sac`, `hiven_comercial` |
| `utm_campaign` | `<contexto>` | Por que mandou. Ex: `indicacao_consultiva`, `recuperacao_carrinho`, `pos_venda_upsell`, `gatilho_d80_refil`, `recompra_automatica` |

### Convenção de naming

- **lowercase + underscore** (não kebab-case, não CamelCase)
- **sem acento** (`recuperacao`, não `recuperação`)
- **sem espaço** (`indicacao_consultiva`, não `indicacao consultiva`)
- **sem caracteres especiais** (sem `?`, `&`, `#`, `/`)

### Exemplos canônicos

```
?utm_source=whatsapp&utm_medium=pedro_vendas&utm_campaign=indicacao_consultiva
?utm_source=whatsapp&utm_medium=sophia_sac&utm_campaign=pos_venda_satisfacao
?utm_source=whatsapp&utm_medium=cron_horario&utm_campaign=carrinho_abandonado
?utm_source=whatsapp&utm_medium=webhook_yampi&utm_campaign=pedido_entregue_avaliacao
?utm_source=whatsapp&utm_medium=cron_d80&utm_campaign=recompra_refil
```

---

## 🛠️ Como aplicar no MCP / workflow

### Caso 1: Tool de catálogo retorna `handle` → agente monta a URL

Tool description tem que dizer **literalmente**:

```
Pra mandar o link ao cliente, monte sempre como:
https://<dominio>/products/{handle}?utm_source=whatsapp&utm_medium=<agente>&utm_campaign=<campanha>
onde {handle} vem do campo 'handle' do produto retornado.
```

O agente é quem concatena. Não tente fazer no n8n com tool — vira fricção.

### Caso 2: Webhook transacional dispara fluxo com link

Code node monta o URL final ANTES de mandar pra NexTags:

```js
const handle = order.line_items[0].sku.data.product_handle;
const checkoutUrl = `https://${dominio}/products/${handle}?utm_source=whatsapp&utm_medium=webhook_${plataforma}&utm_campaign=${evento_normalizado}`;

const actions = [
  { action: 'set_field_value', field_name: 'LinkProduto', value: checkoutUrl },
  // ...
];
```

### Caso 3: Cron de campanha (carrinho abandonado, D+80, etc.)

Mesmo padrão do Caso 2: Code node concatena UTM no link antes de mandar pro NexTags.

```js
// Cron carrinho abandonado
const cartUrl = cart.spreadsheet.data.purchase_url +
  '?utm_source=whatsapp&utm_medium=cron_horario&utm_campaign=carrinho_abandonado';
```

---

## 🚫 Antipadrões — NUNCA fazer

| ❌ Errado | ✅ Certo |
|---|---|
| Link da homepage (`https://veuske.com.br`) | Link do produto específico (`/products/{handle}`) |
| Link sem UTM | Link COM UTM completo (3 parâmetros) |
| Link de categoria (`/collections/aromatizadores`) | Link do produto/kit específico |
| Link encurtado (`bit.ly/...`) | URL completa real do site |
| Link inventado pelo agente (alucinação) | Handle vindo de tool real do MCP |
| UTM com acento ou espaço | UTM lowercase + underscore |
| Agente cita "veuske.com.br" no texto da mensagem | Agente envia apenas o link real, sem citar domínio |

---

## 🔧 Regras pra incluir em TODA tool description que retorna handle/URL

```markdown
IMPORTANTE: para mandar o link ao cliente, monte sempre como:
https://<dominio>/products/{handle}?utm_source=whatsapp&utm_medium=<agente>&utm_campaign=<campanha>

NUNCA invente URL, NUNCA envie homepage solta, NUNCA envie link sem os 3 parâmetros UTM.

Verifique também o campo de disponibilidade (`availableForSale`, `available`, `status`, etc.).
NUNCA indique produto fora de estoque.
```

---

## 🌐 Templates de URL por plataforma

| Plataforma | Padrão de URL de produto | Campo no payload |
|---|---|---|
| Shopify | `https://<shop>.com.br/products/{handle}` | `product.handle` |
| Tray | `https://<shop>.com.br/produto/{slug}` | `product.slug` |
| VTEX | `https://<shop>.com.br/{slug}/p` | `product.linkText` + `/p` |
| Nuvemshop | `https://<shop>.com.br/produtos/{handle}` | `product.handle` |
| Yampi | `https://<shop>.com.br/p/{slug}` | `product.slug` |
| Bling (sem loja própria) | Não envia link de produto — usa link de checkout | — |
| Martz | `https://<shop>.com.br/produto/{slug}` | `product.slug` |
| Shopify checkout direto | `https://<shop>.com.br/cart/{variant_id}:{qty}` | `variant.id` |

Cada um anexa `?utm_source=whatsapp&utm_medium=<agente>&utm_campaign=<campanha>` no final.

---

## ✅ Checklist antes de publicar MCP de Vendas

- [ ] Tool de catálogo retorna `handle`/`slug` real (não vem do prompt hardcoded)
- [ ] Tool description tem a frase exata do "como montar URL com UTM"
- [ ] Tool description proíbe homepage solta
- [ ] Tool description proíbe produto sem estoque (`availableForSale: false`)
- [ ] Agente sabe os 3 valores UTM padrão pra ele (`utm_medium=<nome_agente>`)
- [ ] Agente tem lista de campanhas válidas pra `utm_campaign` (mínimo 2-3 opções)
- [ ] Webhooks transacionais e crons também montam links com UTM no Code node
- [ ] Cliente foi orientado a configurar GA4/Shopify Reports pra filtrar por `utm_source=whatsapp`

---

## 📊 Como validar pós-deploy

Cliente entra no Shopify Reports / GA4:

```
Filter: utm_source = whatsapp
```

Deve aparecer:
- Sessões vindas do WhatsApp
- Receita por `utm_medium` (qual agente converteu mais)
- Receita por `utm_campaign` (qual contexto converteu mais)

Se aparece **vazio** depois de algumas vendas → UTM não está sendo aplicado. Voltar e auditar:
1. Tool description do MCP
2. Code nodes de webhook transacional
3. Code nodes de cron
4. Prompt do agente (talvez ele esteja removendo os parâmetros)

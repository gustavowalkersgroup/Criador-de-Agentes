# Validação de Imagem no MCP — NexTags

> Esta referência é **obrigatória** para qualquer MCP que retorne URL
> de imagem ao agente IA (catálogo de produtos, mídia, banners, etc.).
> A plataforma NexTags só entrega JPEG/PNG nos canais (WhatsApp,
> Instagram, Messenger). WebP, AVIF, SVG e GIF quebram a entrega.

---

## Problema raiz

E-commerces modernos (Shopify, VTEX, Tray, Nuvemshop, Yampi, Yever,
Bling, Martz, etc.) **servem imagem em WebP** por padrão pra economizar
banda. Mesmo quando a URL termina em `.jpg`, o servidor responde:

```
HTTP/1.1 200 OK
Content-Type: image/webp
```

Isso quebra silenciosamente o envio no canal — o agente devolve o JSON
corretamente, mas o WhatsApp/Instagram não consegue renderizar e a
mensagem some.

---

## Estratégias por nível de fidelidade

### Nível 1 — Tool helper que valida HEAD (recomendado)

Adicione uma tool no MCP que faz `HEAD <url>` e devolve o `Content-Type`.
O prompt do agente é instruído a chamar essa tool antes de enviar
qualquer imagem.

```typescript
// assets/image_validator.ts (snippet pra adicionar ao MCP)
{
  name: 'validate_image_url',
  description: 'Valida se a URL retorna JPEG/PNG. Use ANTES de incluir qualquer imagem na resposta.',
  schema: { url: 'string' },
  handler: async ({ url }) => {
    try {
      const res = await fetch(url, { method: 'HEAD', redirect: 'follow' });
      const ct = (res.headers.get('content-type') || '').toLowerCase();
      const ok = ct.startsWith('image/jpeg') || ct.startsWith('image/png');
      return {
        ok,
        content_type: ct,
        recommendation: ok ? 'send_image' : 'omit_image_use_text_only',
      };
    } catch (e) {
      return { ok: false, error: String(e), recommendation: 'omit_image_use_text_only' };
    }
  },
}
```

**Trade-off:** adiciona 1 round-trip HTTP por imagem. Em catálogos
grandes (carrosséis de 10 produtos), pode somar 1–2s. Aceitável pra
agentes conversacionais (não-batch).

---

### Nível 2 — Pré-processar URLs na resposta da tool

Em vez de devolver o `image_url` cru, transformar na própria tool:

1. Fazer HEAD durante o `get_product` / `list_products` / etc.
2. Se `Content-Type` for WebP/AVIF/etc., usar uma das alternativas:
   - Anexar parâmetro de query que força JPEG (depende do CDN):
     - ⚠️ **Shopify: `?format=jpg` NÃO funciona** — testado em produção, o CDN
       ignora o parâmetro e devolve PNG do mesmo jeito (Verdena v2.9). O que
       resolveu foi o sufixo de tamanho (`_600x`) somado a um proxy Cloudinary
       `f_jpg,q_auto` — ver "Shopify CDN" abaixo.
     - VTEX: troca `&fmt=webp` por `&fmt=jpg` (se possível)
     - Cloudinary: insere `/f_jpg/` no path
   - Passar pela URL alternativa de "high quality" que vários CDNs
     expõem como JPEG.
   - Marcar `image_url: null` e adicionar campo `image_warning:
     "WebP rejeitado — usar texto+botão"` na resposta da tool, pra que
     o agente saiba pular a imagem.

**Vantagem:** o agente não precisa pensar em validação, a tool já
entrega URL confiável (ou avisa que não há).

---

### Nível 3 — Avisar no campo de retorno (mínimo viável)

Se não dá pra fazer HEAD (rate limit, latência), pelo menos enriquecer
a resposta da tool com um campo `image_format_hint` baseado em
heurísticas:

```typescript
function imageFormatHint(url: string): string {
  const low = url.toLowerCase();
  const path = low.split('?')[0].split('#')[0];
  const ext = path.slice(path.lastIndexOf('.'));
  if (['.jpg', '.jpeg', '.png'].includes(ext)) return 'likely_jpeg_or_png';
  if (['.webp', '.avif', '.svg', '.gif'].includes(ext)) return 'forbidden_format';
  return 'unknown_validate_before_send';
}
```

O prompt do agente lê esse hint e decide:
- `likely_jpeg_or_png` → enviar normalmente
- `forbidden_format` → omitir imagem
- `unknown_validate_before_send` → omitir imagem (na dúvida, omite)

---

## Quirks por API

| Plataforma | Default | Como forçar JPEG/PNG |
|---|---|---|
| Shopify | WebP/PNG via `image_url` | ⚠️ `?format=jpg` **não funciona** (CDN ignora). Sufixo `_600x` + proxy Cloudinary `f_jpg,q_auto` — ver seção abaixo |
| VTEX | WebP/JPEG variável por loja | Param `&fmt=jpg` (quando suportado), senão HEAD obrigatório |
| Tray | JPEG por padrão | Geralmente OK; ainda assim valide |
| Nuvemshop | WebP comum | HEAD obrigatório; URL `?width=N` às vezes força JPEG |
| Yampi | JPEG comum | OK; valide carrossel |
| Yever | Imagens dinâmicas via Cloudinary | Insere `/f_jpg/` no path do Cloudinary |
| Bling | Imagens base64 ou URL própria | Inspecionar — URL própria normalmente JPEG |
| Martz | Imagens estáticas | Geralmente JPEG; validar mesmo assim |

---

## Como instruir o agente no prompt

O prompt do agente IA deve conter o bloco canônico de validação de
imagem (definido no `nextags-prompt-creator` skill, em
`references/prompt_skeleton.md` → seção "Regras OBRIGATÓRIAS para
imagens").

No bloco "FERRAMENTAS MCP" do prompt, sempre que listar a tool de
catálogo (`get_product`, `search_products`, etc.), adicione:

```
| `validate_image_url` | ANTES de enviar qualquer imagem retornada por outra tool | url da imagem |
```

E na seção de regras de uso da tool de catálogo:

```
- A URL de imagem retornada por `get_product` NÃO é segura — pode ser WebP.
- SEMPRE chame `validate_image_url` antes de incluir a imagem na resposta.
- Se a validação reportar `omit_image_use_text_only`, monte a resposta
  só com texto + botão "Comprar" (sem o attachment image).
```

---

## Princípio operacional

**Na dúvida, omitir.** A ausência da imagem degrada a experiência
visual mas mantém a mensagem entregável. Enviar uma imagem WebP que o
canal rejeita pode resultar em:

- WhatsApp: mensagem completa some — cliente não vê nada.
- Instagram: erro de mídia, mensagem cai.
- Messenger: imagem aparece quebrada (placeholder de erro).

Texto + botão sempre funciona em todos os canais.

---

## Shopify CDN: dois limites do WhatsApp que só aparecem em produção

Formato certo não basta. O CDN da Shopify entrega PNG **16 bits por canal**, de 5 a 15 MB, e
o WhatsApp rejeita nos dois eixos:

| Limite | O que estoura | Sintoma |
|---|---|---|
| **5 MB por imagem** | PNG de catálogo em resolução cheia | a mídia simplesmente não chega |
| **8 bits por canal** | PNG 16-bit da Shopify | rejeitado mesmo abaixo de 5 MB |

O que funcionou em produção (Verdena, hotfixes v2.6 e v2.9): **redimensionar pelo sufixo de
tamanho da própria URL** (`..._600x.png`) e passar por um **proxy Cloudinary com
`f_jpg,q_auto`**, que converte formato e profundidade de cor de uma vez. Resultado medido:
imagem 450× menor, 16-bit → 8-bit.

Não é só validar o formato — é **redimensionar e converter bit-depth** antes de entregar a URL
à IA. Uma tool que devolve `image_url` cru de CDN de e-commerce está entregando uma imagem que
pode não chegar no cliente, e o agente não tem como saber.

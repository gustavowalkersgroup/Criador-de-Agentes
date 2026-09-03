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

## Limites de mídia da Meta — o teto que bloqueia o envio

Formato certo não basta. A Meta bloqueia por **tamanho**, e o bloqueio é seco: **1 MB acima do
limite e a mensagem não sai**.

| Mídia | Teto | O que acontece passando |
|---|---|---|
| **Imagem** | **5 MB** | a Meta bloqueia o envio |
| **Vídeo** | **15 MB** | a Meta bloqueia o envio |

Some-se a isso a **profundidade de cor**: PNG com **16 bits por canal** é rejeitado mesmo
abaixo de 5 MB. Ou seja, três eixos para conferir antes de entregar uma URL à IA — formato
(JPEG/PNG), tamanho e bit-depth.

O caso que fecha os três: o CDN da Shopify entrega PNG 16-bit de 5 a 15 MB. Passa no teste de
formato (é PNG, permitido), estoura o de tamanho e o de bit-depth.

### Como converter — e por que quase nunca é no n8n

A conversão precisa acontecer **na URL**, não dentro do workflow. Motivo: a tool do MCP devolve
um `image_url` em JSON, e quem baixa a imagem depois é a NexTags/WhatsApp — os bytes **nunca
passam pelo n8n**. Converter no n8n só ajuda se o backend baixar, converter e **re-hospedar**,
o que só compensa em acervo fixo (ver `mcp_github_repo_pattern.md`).

**1. Parâmetro do próprio CDN** (de graça, quando existe):

| CDN | Como |
|---|---|
| Shopify | sufixo de tamanho na URL: `..._600x.png` resolve o peso. ⚠️ `?format=jpg` **não funciona** — o CDN ignora |
| VTEX | `&fmt=jpg` no lugar de `&fmt=webp`, quando a loja suporta |
| Cloudinary (loja já usa) | `/f_jpg,q_auto/` no path |
| Nuvemshop | `?width=N` às vezes força JPEG — confirmar com HEAD |

**2. Proxy Cloudinary `fetch`** (resolve formato, qualidade, tamanho e bit-depth de uma vez):

```
https://res.cloudinary.com/<cloud_name>/image/fetch/f_jpg,q_auto,w_1280/<URL_ORIGINAL_ENCODADA>
```

É o que funcionou em produção (Verdena, hotfixes v2.6 e v2.9) para o PNG 16-bit da Shopify:
imagem **450× menor** e 16-bit → 8-bit, sem tocar no workflow. Monte a URL no Code node do slim,
com `encodeURIComponent()` na URL original.

**3. Node `Edit Image` do n8n** (`n8n-nodes-base.editImage`, operações `resize`, `multiStep`,
`information`) — **só quando o workflow tem o binário em mãos**: HTTP Request baixando o
arquivo → Edit Image → upload para onde vai hospedar. Serve para acervo que você controla,
não para catálogo do cliente: fazer isso a cada chamada de tool põe o download da imagem
dentro do tempo de resposta do MCP.

**Vídeo não tem CDN mágico.** Acima de 15 MB, o caminho é re-encodar e hospedar (padrão
GitHub + jsDelivr), porque nenhum parâmetro de URL comprime vídeo. Valide o tamanho **antes**
de cadastrar o vídeo no acervo, não na hora do envio.

Não é só validar o formato — é conferir **formato, tamanho e bit-depth**. Uma tool que devolve
`image_url` cru de CDN de e-commerce está entregando mídia que pode não chegar, e nem o agente
nem o log vão dizer isso.

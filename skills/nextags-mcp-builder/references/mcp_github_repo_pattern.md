# Padrão GitHub-como-banco-de-dados (cliente sem ERP/API)

> **Referência:** Poé Backend Buscar Mídia (`kyLZitHeBz7PXXwp`, corpus de 21 workflows n8n em produção) + MCP Poé
> (`lk0lpDShxXFGia7D`).
> Use quando o cliente **não tem** ERP ou sistema com API para consultar catálogo, mídias,
> FAQ ou tabela de preços — e esse conteúdo é **razoavelmente estável** (não muda a cada
> minuto).

---

## 1. Quando usar

- Cliente sem ERP/plataforma de e-commerce com API própria (não é o caso comum de
  Shopify/VTEX/Tray — ali a API real da plataforma é a fonte).
- Conteúdo é **catálogo de mídias** (vídeos de vendas, PDFs, imagens), **FAQ** ou **tabela
  de preços/condições** que muda por decisão humana esporádica, não em tempo real.
- Não usar para dado que muda a cada pedido/estoque em tempo real — isso precisa de API
  real (ver `arquitetura_padrao.md` Casos A-C).

---

## 2. Estrutura do repositório

Repo GitHub (público, ou privado com token de leitura), 1 arquivo `catalogo.json` na raiz
+ mídias versionadas por commit. Nome do repo: `<owner>/<cliente>-<dominio>` (ex.:
`gustavowalkersgroup/poe-midias`).

### Campos do `catalogo.json` (confirmados em produção — não inventar além destes)

```
{
  "ativos": [
    {
      "id": "...",
      "nome": "...",
      "tipo": "...",
      "disponivel": true,
      "quando_usar": "...",
      "itens": [
        { "url": "...", "duracao_s": 0, "excede_limite_whatsapp": false }
      ],
      "etapa": "...",
      "etapas_extra": ["..."],
      "perfis": ["..."],
      "origens": ["..."],
      "objecoes": ["..."],
      "agente": ["..."],
      "tags": ["..."],
      "uso_interno": false,
      "uso_unico": false,
      "aviso": "...",
      "motivo_indisponivel": "...",
      "formato_envio": "..."
    }
  ]
}
```

| Campo | Papel |
|---|---|
| `id`, `nome`, `tipo` | identificação do ativo |
| `disponivel` | bool — controla se a mídia pode ser oferecida agora |
| `quando_usar` | texto curto — o agente lê pra decidir contexto de uso |
| `itens[]` | os arquivos de fato: `url`, `duracao_s` (vídeo/áudio), `excede_limite_whatsapp` (arquivo grande demais — instrui NÃO enviar) |
| `etapa` / `etapas_extra[]` | filtro por etapa da conversa/funil |
| `perfis[]`, `origens[]`, `objecoes[]`, `agente[]`, `tags[]` | filtros combináveis de contexto |
| `uso_interno` | true = nunca sai pro cliente, filtrado no backend antes de responder |
| `uso_unico` | true = não repetir pra mesma pessoa |
| `aviso` | nota de instrução extra pro agente sobre este ativo |
| `motivo_indisponivel` | texto pronto quando `disponivel:false` |
| `formato_envio` | ativo que não é arquivo (ex.: vai como texto/botão `web_url`, nunca como attachment) |

Não adicionar campo que não está nesta lista sem confirmar com o dono — o corpus de
evidência (Poé) só cobre estes.

---

## 3. Leitura: jsDelivr, NUNCA raw.githubusercontent

```
https://cdn.jsdelivr.net/gh/<owner>/<repo>@main/catalogo.json
```

`raw.githubusercontent.com` serve binário como `application/octet-stream` — WhatsApp
rejeita `.mp4` entregue com esse Content-Type (medido 2026-08-31; ver
`quirks_n8n.md` Quirk #29). jsDelivr serve o Content-Type correto (`video/mp4`,
`image/jpeg`, `audio/ogg`) a partir do mesmo repositório, sem mudar nada no conteúdo.

Se o repo for privado, jsDelivr não serve — nesse caso, ler via API do GitHub
(`GET /repos/<owner>/<repo>/contents/catalogo.json` com `Accept:
application/vnd.github.raw` + token de leitura) em vez de jsDelivr.

---

## 4. Backend n8n

```
Webhook (POST, filtros no body — todos opcionais e combináveis)
  ↓
HTTP GET jsDelivr  (retryOnFail: true, maxTries: 3, waitBetweenTries: 2000,
                     onError: continueRegularOutput — nunca derruba o webhook)
  ↓
Code node: filtra `ativos` pelos filtros recebidos (etapa/perfil/origem/objecao/
           agente/termo, case/trim normalizado), remove `uso_interno: true`,
           "enxuga" pro agente (id, nome, tipo, disponivel, quando_usar + campos
           condicionais)
  ↓
Resposta com AÇÃO EXPLÍCITA pro agente, não só dado cru:
  - disponivel:false  → {"acao": "NAO prometa nem mencione esta mídia. Entregue
                          o equivalente em texto e siga a conversa normalmente."}
  - erro_tecnico:true → catálogo não carregou (`cat.ativos` não é array) — devolve
                         mensagem pra NÃO prometer envio de mídia, seguir só em
                         texto. NUNCA inventa URL.
  - uso_unico:true    → instrução pra não repetir pra mesma pessoa
  - excede_limite_whatsapp:true → instrução pra não enviar, oferecer alternativa
  - múltiplos arquivos → nota_envio: "envie UM por vez, nunca dispare todos juntos"
```

(evidência: Poé Backend Buscar Mídia `kyLZitHeBz7PXXwp`)

### Filtros aceitos no body (todos opcionais)

`id | etapa | perfil | origem | objecao | agente | termo`

---

## 5. Tools do MCP

Padrão igual ao resto da skill: `n8n-nodes-base.httpRequestTool` v4.4/v4.5 com
`$fromAI(...)` por parâmetro, chamando o backend pela **URL interna**
(`http://n8n:5678/webhook/<path>` — a pública dá connection refused de dentro do n8n, ver
`quirks_n8n.md` Quirk #31). Nunca `toolWorkflow` nem `toolHttpRequest` +
`placeholderDefinitions` (Quirk #30).

Tool description segue `tool_descriptions_guide.md`: quando usar, quando NÃO usar,
parâmetros (todos opcionais), retorno, e o bloco de COMPORTAMENTO cobrindo
`disponivel:false` e `erro_tecnico:true` explicitamente — o agente precisa saber que a
resposta às vezes é uma instrução ("não prometa"), não um dado a repassar cru.

---

## 6. Trocar mídia = commit no repo

Nada muda no n8n nem no prompt do agente pra atualizar catálogo, preço ou disponibilidade —
só um commit no `catalogo.json` (e upload do arquivo, se for mídia nova). É o benefício
central do padrão: o cliente (ou o time Walkers) edita o repositório, o backend já lê a
versão nova na próxima chamada.

---

## 7. Checklist de setup pro cliente

- [ ] Repositório criado (público, ou privado + token de leitura guardado no n8n)
- [ ] `catalogo.json` na raiz, validado como JSON (sem vírgula sobrando)
- [ ] Definido quem faz commit (Walkers ou o próprio cliente) e como (direto no GitHub, ou
      via planilha que gera o JSON — fora do escopo desta skill)
- [ ] Backend testado: `curl` no endpoint do webhook com pelo menos 1 filtro de cada tipo
- [ ] MIME validado com chamada real: `curl -I https://cdn.jsdelivr.net/gh/<owner>/<repo>@main/<arquivo>`
      — confirmar `Content-Type: video/mp4` (ou o tipo esperado), nunca
      `application/octet-stream`
- [ ] Testado o caminho de erro: renomear/apagar temporariamente o `catalogo.json` local
      (branch de teste) e confirmar que o backend devolve `erro_tecnico:true` em vez de
      quebrar o webhook
- [ ] Tool description do MCP cobre `disponivel:false` e `erro_tecnico:true` explicitamente

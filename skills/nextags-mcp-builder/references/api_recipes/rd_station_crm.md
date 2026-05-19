# RD Station CRM (v2)

> Status: 🟡 stub (preencher na primeira integração real)
> Última atualização: Maio/2026
> Cliente(s) usando: (nenhum ainda)

## 🔗 Base URL e ambientes

- **Produção:** `https://crm.rdstation.com/api/v1/`
- **Doc:** https://developers.rdstation.com/reference/crm-v2-introduction (mesmo nome "v2" mas path é `/v1/`)

## 🔐 Autenticação

**Tipo: A — token fixo via query param**

```
GET .../endpoint?token={token}
```

- **Credencial n8n:** `httpQueryAuth` com Name=`token`, Value=`<api_key>`
- **Como obter:** Admin do RD Station CRM → Configurações → Integrações → API → Token

## 📦 Endpoints essenciais (a validar na primeira integração)

Diferente de e-commerce, RD CRM é CRM B2B/SaaS. Foco diferente:

- `GET /contacts` — listar contatos
- `GET /contacts/{id}` — detalhe contato
- `POST /contacts` — criar contato (lead capture)
- `GET /deals` — listar negócios (oportunidades)
- `GET /deals/{id}` — detalhe deal
- `GET /activities` — atividades (calls, emails, reuniões)
- `GET /campaigns` — campanhas
- `GET /tags` — tags

## ⚠️ Quirks (a preencher)

- Auth via QUERY (não header) é incomum hoje — atenção pra logging que pode expor o token
- Rate limit?
- Formato de IDs?
- Shape de resposta (wrapper `data`/`items`?)

## 🛡️ Mapeamento operações comuns → endpoints

| Caso de uso | Endpoint candidato |
|---|---|
| Buscar contato por email | `GET /contacts?email=` (verificar) |
| Detalhe contato | `GET /contacts/{id}` |
| Listar deals do contato | (a verificar) |
| Criar lead | `POST /contacts` |
| Atualizar tags | `PATCH /contacts/{id}/tags` (a verificar) |

## 📋 Decisão de arquitetura

Caso A — token fixo via query. Tools `httpRequestTool` direto.

⚠️ **Atenção:** RD CRM é CRM, não e-commerce. Casos de uso são diferentes:
- **Atendimento B2B:** buscar contato, ver deals abertos, atualizar status
- **Lead generation:** capturar contato novo via chat → criar no CRM
- **Não há catálogo de produtos no sentido tradicional**

Pra MCPs futuros que envolvam RD CRM, esperar briefing específico (não é loja).

## 🔗 Links

- Doc: https://developers.rdstation.com/reference/crm-v2-introduction
- Última visita: Maio/2026 (resumida, não fetchada em profundidade)

## 📝 Notas

- Stub. Encontrei via referência da lista de APIs do time NexTags. Validar na primeira oportunidade.

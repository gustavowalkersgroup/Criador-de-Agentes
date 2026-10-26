# Tokens reais em docs da skill (regra inegociável)

> Movido de `SKILL.md` sem alteração de conteúdo. O resumo e o auto-check ficam no `SKILL.md`.

### 🔐 Mas NUNCA escreva tokens reais em docs da skill

Esta skill é versionada no GitHub. **Qualquer arquivo em `references/`, `assets/` ou `api_recipes/` é público.** Tokens reais nesses arquivos:

- ❌ São bloqueados pelo Secret Scanning do GitHub na hora do push
- ❌ Quando passam, ficam expostos no histórico git pra sempre (mesmo após `git rm`)
- ❌ Exigem revogação + rotação do token comprometido

**Regra absoluta:** quando documentar um exemplo em recipe/quirks/pattern que envolve token, use placeholder no formato `<tipo>_<descrição>`. Exemplos:

| ❌ Errado (token literal de produção) | ✅ Certo (placeholder) |
|---|---|
| `value: 'shpat_<TOKEN_LITERAL_AQUI>'` | `value: 'shpat_<32-hex-do-cliente>'` |
| `Client Secret: shpss_<SECRET_LITERAL>` | `Client Secret: shpss_<32-hex>` (não colar em docs) |
| `X-ACCESS-TOKEN: <NEXTAGS_LITERAL>` | `X-ACCESS-TOKEN: <NEXTAGS_ACCESS_TOKEN>` |
| `User-Token: <YAMPI_LITERAL>` | `User-Token: <YAMPI_USER_TOKEN>` |

**Onde tokens reais ficam:**
- ✅ Workflows n8n (hardcoded em `headerParameters` — privado da instância n8n)
- ✅ Data tables n8n (`Shopify Tokens`, `<Cliente> API Keys`, etc.)
- ✅ Memórias de projeto (`C:\Users\User\.claude\projects\<projeto>\memory\*.md`) — fica só na sua máquina, fora do git da skill
- ✅ Relatórios do cliente (`C:\Users\User\Documents\WALKERS\<cliente>\*.md`) — fora do git da skill

**Auto-check antes de comitar mudanças na skill:**

```bash
grep -rE 'shpat_[a-f0-9]{32}|shpss_[a-f0-9]{32}|shpca_[a-f0-9]+|atkn_|TR56[a-zA-Z0-9]{30,}|sk_[a-zA-Z0-9]{30,}|[0-9]{7}\.[a-zA-Z0-9]{30,}' references/ assets/
```

Se retornar algo, mascara antes de comitar.

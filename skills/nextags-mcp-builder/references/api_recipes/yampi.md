# Yampi

> Status: 🟡 stub (preencher na primeira integração real)
> Última atualização: Maio/2026
> Cliente(s) usando: (nenhum ainda)

## 🔗 Base URL e ambientes

- **Produção:** `https://api.dooki.com.br/v2/{alias}/`
- **`{alias}`:** identificador da loja na Yampi (subdomínio)
- **Doc:** https://docs.yampi.com.br/introduction

## 🔐 Autenticação

**Tipo: A — chave + token em 2 headers**

```
User-Token: <token>
User-Secret-Key: <secret>
```

- **Credencial n8n:** `httpCustomAuth` com JSON dos 2 headers:
  ```json
  {
    "headers": {
      "User-Token": "<token>",
      "User-Secret-Key": "<secret>"
    }
  }
  ```
- **Como obter:** Admin Yampi → Aplicativos → criar app → copiar `User-Token` e `User-Secret-Key`

(Mesma situação da VTEX: 2 headers, exige `httpCustomAuth`.)

## 📦 Endpoints essenciais (a validar)

Yampi é plataforma de e-commerce BR similar a Tray/Nuvemshop.

- `GET /catalog/products?q={termo}` — buscar produtos
- `GET /catalog/products/{id}` — detalhe
- `GET /orders?q={termo}` — buscar pedido
- `GET /orders/{id}` — detalhe
- `GET /customers?email={email}` — buscar cliente
- `GET /customers/{id}` — detalhe

(Endpoints exatos a confirmar na doc oficial.)

## ⚠️ Quirks (a preencher)

- Preço em centavos ou reais?
- Paginação?
- Estoque por SKU/variação?
- Rate limit?

## 🛡️ Mapeamento operações comuns → endpoints

(A preencher no primeiro uso real.)

## 📋 Decisão de arquitetura

Caso A — duas keys fixas. `httpCustomAuth`. Tools direto.

## 🔗 Links

- Doc: https://docs.yampi.com.br/introduction
- Última visita: Maio/2026 (resumida)

## 📝 Notas

- Stub. Validar quando aparecer cliente Yampi real.

# Documentação da API Zoppy Partners

## 🏠 Início

Integre sua plataforma com a Zoppy e potencialize o relacionamento com seus clientes.

## 🔑 Autenticação

Nossa autenticação é do tipo `Authorization: Bearer Token`.

### Cadastro de Parceiros

Para iniciar uma nova integração, entre em contato com o time da Zoppy para prosseguir com o cadastro de parceiros integradores: `contato@zoppy.com.br`

### Base URL

Nossa URL base de acesso é `https://api-partners.zoppy.com.br`, seguido do sufixo `/api` para todas as chamadas.

Exemplo:
`GET https://api-partners.zoppy.com.br/api/products`

### Configuração

Para obter o seu token, basta ir na plataforma da Zoppy, menu principal superior a direita → Chave de API, e copiar o token.

`Authorization: Bearer seu_token_aqui`

### Requests

Nos headers, basta inserir o Header `Authorization: Bearer {seu_token}`.

```json
{
   "headers" : {
     "Authorization" :  "Bearer seu_token_aqui" ,
     "Content-Type" :  "application/json" 
  }
}
```

### Listas Paginadas

Todo método que retorna uma lista, retorna uma lista paginada. O request obrigatoriamente deverá possuir os campos:

| Propriedade | Tipo | | Descrição |
| --- | --- | --- | --- |
| `after` | Date | Obrigatório | Data de referência para paginação (ISO 8601) |
| `page` | number | Obrigatório | Número da página |
| `pageSize` | number | Obrigatório | Quantidade de itens por página |
| `updatedAt` | string | Opcional | Filtrar por data de atualização |

```json
{
   "after" :  "2024-01-01T00:00:00.000Z" ,
   "page" :  1 ,
   "pageSize" :  20 
}
```

Quer testar os recursos sem montar as requests manualmente? Acesse nosso Swagger diretamente.

## 📦 Produtos

`/api/products`

Gerencie os produtos da sua loja. Cada produto pode ter categorias, preço, status e especificação.

### Modelo

| Propriedade | Tipo | | Descrição |
| --- | --- | --- | --- |
| `id` | string | Obrigatório | ID único do produto (UUID) |
| `externalId` | string | Opcional | ID do produto no seu sistema/provedor |
| `name` | string | Obrigatório | Nome do produto |
| `status` | string | Obrigatório | Status do produto (publish, draft, inactive) |
| `specification` | string | Opcional | Especificação do produto (m, f) |
| `price` | number | Obrigatório | Preço do produto |
| `categories` | string[] | Opcional | Lista de categorias |
| `provider` | string | Opcional | Identificador do sistema que integra |
| `createdAt` | Date | Obrigatório | Data de criação |
| `updatedAt` | Date | Obrigatório | Data de atualização |

### Endpoints

*   `GET /api/products/` Listar produtos
*   `GET /api/products/:id` Buscar produto por ID
*   `GET /api/products/name/:name` Buscar produto por nome
*   `GET /api/products/external/:externalId` Buscar produto por ID externo
*   `POST /api/products/` Criar produto
*   `PUT /api/products/:id` Atualizar produto
*   `DELETE /api/products/:id` Deletar produto

## 👥 Clientes

`/api/customers`

Gerencie os clientes da sua loja. Clientes podem ter endereço, cupons e campos personalizados.

### Modelo

| Propriedade | Tipo | | Descrição |
| --- | --- | --- | --- |
| `id` | string | Obrigatório | ID único do cliente (UUID) |
| `externalId` | string | Opcional | ID do cliente no seu sistema/provedor |
| `email` | string | Opcional | Email do cliente |
| `phone` | string | null | Opcional | Telefone do cliente (formato brasileiro, 11 dígitos) |
| `firstName` | string | Obrigatório | Primeiro nome |
| `lastName` | string | Obrigatório | Sobrenome |
| `birthDate` | Date | null | Opcional | Data de nascimento |
| `gender` | string | null | Opcional | Gênero. Valores: m, f |
| `position` | string | null | Opcional | Segmentação RFM (somente leitura). Valores: promising, loyal, sleeping, possible-loyal, at-risk |
| `address` | AddressResponse | null | Opcional | Endereço do cliente (id, address1, address2, city, state, postcode, country, latitude, longitude) |
| `coupon` | CouponResponse | Opcional | Cupom vinculado ao cliente |
| `customFields` | CustomerCustomFieldResponse[] | Opcional | Campos personalizados do cliente |
| `createdAt` | Date | Obrigatório | Data de criação |
| `updatedAt` | Date | Obrigatório | Data de atualização |

### Endpoints

*   `GET /api/customers/` Listar clientes
*   `GET /api/customers/:id` Buscar cliente por ID
*   `GET /api/customers/phone/:phone` Buscar cliente por telefone
*   `GET /api/customers/external/:externalId` Buscar cliente por ID externo
*   `POST /api/customers/` Criar cliente
*   `PUT /api/customers/:id` Atualizar cliente
*   `DELETE /api/customers/:id` Deletar cliente

## 🛒 Pedidos

`/api/orders`

Gerencie os pedidos da sua loja. Pedidos podem conter itens, cupons, informações de loja e vendedor.

### Modelo

| Propriedade | Tipo | | Descrição |
| --- | --- | --- | --- |
| `id` | string | Obrigatório | ID único do pedido (UUID) |
| `externalId` | string | Opcional | ID do pedido no seu sistema/provedor |
| `status` | string | Obrigatório | Status do pedido (completed, canceled, on-hold, processing) |
| `subtotal` | number | Obrigatório | Subtotal (antes do desconto) |
| `total` | number | Obrigatório | Total final do pedido |
| `discount` | number | Opcional | Valor total do desconto |
| `shipping` | number | Opcional | Custo do frete |
| `couponCode` | string | Opcional | Código do cupom utilizado |
| `completedAt` | Date | Opcional | Data de conclusão do pedido |
| `provider` | string | Opcional | Identificador do provedor de integração |
| `customerId` | string | Obrigatório | ID do cliente |
| `storeId` | string | Opcional | ID da loja |
| `userId` | string | Opcional | ID do usuário vendedor |
| `customer` | CustomerResponse | Obrigatório | Dados completos do cliente |
| `lineItems` | LineItemResponse[] | Opcional | Itens do pedido (com produto incluso) |
| `couponCreated` | CouponResponse | Opcional | Cupom criado por este pedido |
| `couponUsed` | CouponResponse | Opcional | Cupom utilizado neste pedido |
| `createdAt` | Date | Obrigatório | Data de criação |
| `updatedAt` | Date | Obrigatório | Data de atualização |

### Endpoints

*   `GET /api/orders/` Listar pedidos
*   `GET /api/orders/:id` Buscar pedido por ID
*   `GET /api/orders/external/:externalId` Buscar pedido por ID externo
*   `POST /api/orders/` Criar pedido
*   `PUT /api/orders/:id` Atualizar pedido
*   `DELETE /api/orders/:id` Deletar pedido

## 🎟️ Cupons

`/api/coupons`

Gerencie cupons de desconto. Suporta cupons individuais (vinculados a um cliente) e compartilhados (shared, com limite de uso).

### Modelo

| Propriedade | Tipo | | Descrição |
| --- | --- | --- | --- |
| `id` | string | Obrigatório | ID único do cupom (UUID) |
| `externalId` | string | null | Opcional | ID do cupom no seu sistema/provedor |
| `code` | string | Obrigatório | Código do cupom |
| `type` | string | Opcional | Tipo do cupom. Valores: percent (percentual), fixed_cart (valor fixo) |
| `amount` | number | Obrigatório | Valor do desconto |
| `used` | boolean | Obrigatório | Se o cupom foi utilizado |
| `isValid` | boolean | Obrigatório | Se o cupom está válido |
| `minPurchaseValue` | number | Opcional | Valor mínimo de compra para uso |
| `expiryDate` | Date | Obrigatório | Data de expiração |
| `startDate` | Date | Obrigatório | Data de início de validade |
| `customer` | CustomerResponse | Opcional | Cliente vinculado (apenas cupons individuais) |
| `usageLimit` | number | Opcional | Limite de uso (apenas cupons compartilhados) |
| `createdAt` | Date | Obrigatório | Data de criação |
| `updatedAt` | Date | Obrigatório | Data de atualização |

### Endpoints

*   `GET /api/coupons/:id` Buscar cupom por ID
*   `GET /api/coupons/code/:code` Buscar cupom por código
*   `GET /api/coupons/order/:orderId` Buscar cupom criado pelo pedido
*   `GET /api/coupons/external/:externalId` Buscar cupom por ID externo
*   `GET /api/coupons/phone/:phone` Buscar cupom por telefone
*   `GET /api/coupons/phone/:phone/many` Buscar vários cupons por telefone
*   `POST /api/coupons/` Criar cupom individual
*   `POST /api/coupons/shared` Criar cupom compartilhado
*   `POST /api/coupons/resend` Reenviar cupons
*   `PUT /api/coupons/:id` Atualizar cupom por ID
*   `PUT /api/coupons/code/:code` Atualizar cupom por código
*   `PUT /api/coupons/phone/:phone` Atualizar cupom por telefone
*   `PUT /api/coupons/externalId/:externalId` Atualizar cupom por ID externo
*   `DELETE /api/coupons/:id` Deletar cupom por ID
*   `DELETE /api/coupons/code/:code` Deletar cupom por código
*   `DELETE /api/coupons/phone/:phone` Deletar cupom por telefone
*   `DELETE /api/coupons/externalId/:externalId` Deletar cupom por ID externo

## 🏪 Lojas

`/api/stores`

Gerencie as lojas vinculadas à sua empresa.

### Modelo

| Propriedade | Tipo | | Descrição |
| --- | --- | --- | --- |
| `id` | string | Obrigatório | ID único da loja (UUID) |
| `externalId` | string | Opcional | ID da loja no seu sistema/provedor |
| `name` | string | Obrigatório | Nome da loja |
| `isEcommerce` | boolean | Opcional | Se a loja é um e-commerce |
| `createdAt` | Date | Obrigatório | Data de criação |
| `updatedAt` | Date | Obrigatório | Data de atualização |

### Endpoints

*   `GET /api/stores/` Listar lojas
*   `GET /api/stores/:id` Buscar loja por ID
*   `GET /api/stores/external/:externalId` Buscar loja por ID externo
*   `POST /api/stores/` Criar loja
*   `PUT /api/stores/:id` Atualizar loja
*   `DELETE /api/stores/:id` Deletar loja

## 👤 Usuários

`/api/users`

Gerencie os usuários da sua empresa.

### Modelo

| Propriedade | Tipo | | Descrição |
| --- | --- | --- | --- |
| `id` | string | Obrigatório | ID único do usuário (UUID) |
| `name` | string | Obrigatório | Nome completo |
| `userName` | string | Opcional | Nome de usuário |
| `nickName` | string | Opcional | Apelido |
| `email` | string | Obrigatório | Email |
| `role` | string | Opcional | Papel do usuário |
| `createdAt` | Date | Obrigatório | Data de criação |
| `deletedAt` | Date | null | Opcional | Data de exclusão (null se ativo) |

### Endpoints

*   `GET /api/users/` Listar usuários
*   `GET /api/users/count` Contar usuários da empresa
*   `GET /api/users/:id` Buscar usuário por ID
*   `GET /api/users/email/:email` Buscar usuário por email
*   `POST /api/users/` Criar usuário
*   `DELETE /api/users/:id` Deletar usuário

## 🛍️ Carrinhos Abandonados

`/api/abandoned-carts`

Gerencie os carrinhos abandonados para recuperação de vendas.

### Modelo

| Propriedade | Tipo | | Descrição |
| --- | --- | --- | --- |
| `id` | string | Obrigatório | ID único (UUID) |
| `externalId` | string | Opcional | ID da entidade no seu sistema/provedor |
| `url` | string | Opcional | URL do carrinho abandonado |
| `subtotal` | number | Obrigatório | Subtotal |
| `total` | number | Obrigatório | Total |
| `discount` | number | Opcional | Desconto |
| `shipping` | number | Opcional | Frete |
| `customerId` | string | Obrigatório | ID do cliente |
| `customer` | CustomerResponse | Obrigatório | Dados completos do cliente |
| `lineItems` | LineItemResponse[] | Opcional | Itens do carrinho |
| `createdAt` | Date | Obrigatório | Data de criação |
| `updatedAt` | Date | Obrigatório | Data de atualização |

### Endpoints

*   `GET /api/abandoned-carts/` Listar carrinhos abandonados
*   `GET /api/abandoned-carts/:id` Buscar carrinho por ID
*   `GET /api/abandoned-carts/external/:externalId` Buscar carrinho por ID externo
*   `POST /api/abandoned-carts/` Criar carrinho abandonado
*   `PUT /api/abandoned-carts/:id` Atualizar carrinho
*   `DELETE /api/abandoned-carts/:id` Deletar carrinho

## 🔔 Webhooks

`/api/webhooks`

Configure webhooks para receber notificações de eventos da Zoppy. Atualmente suporta o evento `coupon_create`.

### Modelo

| Propriedade | Tipo | | Descrição |
| --- | --- | --- | --- |
| `id` | string | Obrigatório | ID único do webhook (UUID) |
| `event` | string | Obrigatório | Tipo do evento |
| `url` | string | Obrigatório | URL de destino do webhook |
| `bearerToken` | string | Opcional | Token de autenticação para o endpoint de destino |

### Endpoints

*   `GET /api/webhooks/` Listar webhooks
*   `POST /api/webhooks/` Criar webhook
*   `PUT /api/webhooks/:id` Atualizar webhook
*   `DELETE /api/webhooks/:id` Deletar webhook

## 🏷️ Campos Personalizados

`/api/custom-field`

Gerencie campos personalizados de clientes. Os campos possuem versionamento — cada atualização cria uma nova versão.

### Modelo

| Propriedade | Tipo | | Descrição |
| --- | --- | --- | --- |
| `id` | string | Obrigatório | ID do campo personalizado |
| `name` | string | Obrigatório | Nome interno do campo |
| `displayName` | string | Obrigatório | Nome de exibição do campo |
| `phone` | string | Obrigatório | Telefone do cliente vinculado |
| `type` | string | Obrigatório | Tipo do campo |
| `valueType` | string | Obrigatório | Tipo do valor (string, number, date, boolean) |
| `companyId` | string | Obrigatório | ID da empresa |
| `customerId` | string | Obrigatório | ID do cliente |
| `parentId` | string | Obrigatório | ID do campo pai |
| `latestVersion` | object | Obrigatório | Última versão do valor. Campos: { id, numberValue, stringValue, dateValue, booleanValue, mask, valueType, isCurrent, version, customFieldId } |

### Endpoints

*   `POST /api/custom-field/` Criar campo personalizado (template)
*   `GET /api/custom-field/customer/:customerId` Buscar campos por ID do cliente
*   `GET /api/custom-field/phone/:phone` Buscar campos por telefone
*   `POST /api/custom-field/version` Criar nova versão de campo
*   `DELETE /api/custom-field/` Deletar campos personalizados

## 🏢 Empresa

`/api/companies`

Consulte informações da sua empresa. A empresa é identificada automaticamente pelo token de autenticação.

### Modelo

| Propriedade | Tipo | | Descrição |
| --- | --- | --- | --- |
| `id` | string | Obrigatório | ID da empresa (UUID) |
| `status` | string | Obrigatório | Status da empresa |

### Endpoints

*   `GET /api/companies/` Buscar minha empresa

## ⚡ Swagger UI

Interactive API explorer

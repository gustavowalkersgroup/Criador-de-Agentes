# Antipadrões de webhook transacional NexTags — catálogo de erros reais

> Todos observados em produção ou nas conversas. Cada um custou tempo. Evite-os no setup.

## 1. Texto direto em vez de `send_flow` (o pior)

A plataforma NexTags **nunca processa texto solto** — trava o fluxo. Disparo proativo é sempre `send_flow`.

| Caso real | O que aconteceu | Como evitar |
|---|---|---|
| **Closet FIT** | Exemplos de JSON no prompt estavam em fences ` ```json `; o modelo copiou o fence no runtime → JSON vazou como texto cru pro cliente | **Nunca** envolver exemplos JSON em fences markdown no prompt — usar separadores em prosa (few-shot dominance: examples > rules) |
| **DOLPS** | Agente entregou chave de NF-e (44 díg.) como texto + "consulte manualmente" em vez de rotear | Quando o dado cru não resolve o problema, **rotear pra humano via `send_flow`** — não despejar texto |
| **Wazzu** | `text` mandado como `{body:...}` (formato interno WhatsApp Cloud API) | `text` é **string direta**, sempre. `{body}` é o que o middleware NexTags gera, não o que você manda |
| **Wazzu** | "JSON virou texto bruto na 2ª execução" | Causa no **pipeline do n8n** (onde a resposta é salva/reenviada), não no formato — investigar o pipeline antes de mexer no JSON |
| **Veuske** | "Transferência fantasma": IA dizia "vou te direcionar" mas o `send_flow` não disparava | Anti-loop/transferência deve checar o **CUF gravado no momento do disparo**, não o texto da resposta |
| **Amo Calçados** (n8n) | Workflow envia texto livre direto ao cliente | Sempre `send_flow`; texto é tipo de mensagem dentro do flow, não saída livre |

## 2. `set_field_value` depois de `send_flow`

Ordem errada no `actions[]` faz os CUFs chegarem **vazios** no destino da transferência/flow. **`set_field_value` SEMPRE antes de `send_flow`.** (DOLPS "Regra 16")

## 3. Confiar no `success:true` do `send_flow`

`/send/{flow_id}` retorna `success:true` **mesmo para flow_id inexistente/falso** (Alto Giro). Nunca use a resposta da API como prova de entrega — valide com recebimento real no WhatsApp. E o endpoint exige `Content-Length > 0` (retorna **411** se o corpo vier vazio).

## 4. Placeholder de flow_id shippado em produção

- Dolps v1: `flow_id = 11111111111` nas 4 branches (placeholder nunca substituído).
- Viens: `flow_id = COLE_O_FLOW_ID`.
Resultado: disparo no-op ou erro silencioso. **Sempre preencher o flow_id real e validar E2E antes de ativar.**

## 5. Dedup em memória (não persiste)

- Viens: `sd.seen = {[order_id]: true}` num objeto de execução, sobrescrito a cada run → dedup quebrado, cliente recebe repetido.
**Dedup sempre em Data Table.** Nunca variável in-memory.

## 6. Copy-paste entre clientes sem trocar referências (causa nº1 de disparo fantasma)

- **Wazzu:** clonou workflow da **Hebreus Doze** e deixou o `X-ACCESS-TOKEN` (conta 1636393) e a Data Table de dedup apontando pra conta/loja errada → `send_flow` retornava success mas era **no-op na conta errada**.
- **Vitabe:** função `formatarNPedido` removia prefixo `RENOVABE-` (nome de **outro** cliente) — código herdado sem adaptar; corrompe o número do pedido.

**Ao clonar, troque TUDO:** token/conta, Data Table de dedup, `field_name` dos CUFs, `flow_id`, e nomes de node.

## 7. CUF tipo NÚMERO

CUF criado como tipo **NÚMERO** no NexTags faz `set_field_value` **descartar o valor silenciosamente** (sem erro). Todo CUF setado via `/api/contacts` deve ser **TEXTO**. (Mayuí)

## 8. Variável de template vazia derruba o flow inteiro

WhatsApp `#131008`: se **qualquer** CUF interpolado num template estiver vazio, o envio do template **inteiro** falha. Garanta 100% das variáveis preenchidas antes do `send_flow` (ou tenha variante neutra). (Mayuí)

## 9. `order_number` como chave de dedup

`order_number` (número visível) pode repetir/ser reusado. Use **`order_id` interno** como chave; se precisar do número, use chave composta `order_id + status` (Veuske usa `nPedido + idPedido`). Nunca dedup só por `order_number`.

## 10. Assumir gatilho errado por plataforma

- Fazer **cron** de carrinho onde a plataforma **emite webhook** (Yampi emite webhook de abandono — erro corrigido na Veuske).
- Assumir **webhook** onde só há **polling** (Magazord, Conecta Venda não têm webhook).
Sempre confirmar na doc da plataforma.

## 11. `body.event` em vez de `status.alias` no Switch

Rotear por `body.event` quebra quando a plataforma manda 1 evento genérico com status variável. Switch por `resource.status.data.alias`/`status.name` — mais robusto. (referência Rafa/Veuske)

## 12. httpRequest v4.4 com body errado

`jsonParameters`/`bodyParametersJson` **não serializa** o body → POST /contacts falha com falso `"Invalid phone number"`. Use `specifyBody:'json'` + `jsonBody`. (Alto Giro)

## 13. Sem guard de telefone / sem retry

- Sem guard de telefone → item sem telefone corrompe o contato ou falha o envio (Iorane, Bem Beleza, Wazzu, Vitabe, BB).
- Sem `retryOnFail` → falha transitória do NexTags perde a notificação **e** o INSERT de dedup (Alto Giro, Amo, Privilège, HIVEN, Iorane, Boca Rosa, Bem Beleza).

## 14. Concatenar query string sem checar `?`

Colar `&utm_source=...` num link que ainda não tem `?` gera URL quebrada (bug real no `link_checkout_abandono` da Mayuí). Checar/normalizar antes.

## 15. Número de pedido calculado e descartado

Boca Rosa calcula `numero_pedido` no Code node e o node seguinte nunca usa — o CUF nunca é setado. Verifique que o valor computado realmente entra no `actions[]`.

---
name: nextags-webchat-tester
description: "Testa um agente de webchat NexTags (plataforma tapthetable) AO VIVO, dirigindo o WebSocket do webchat por Python — sem extensão do Chrome e sem simular 'no córtex'. Exercita a stack REAL publicada (modelo do NexTags + MCP + APIs de backend tipo Nuvemshop/Bling/Shopify). Use sempre que o usuário quiser TESTAR/VALIDAR/conversar com o bot PUBLICADO via webchat, confirmar que uma mudança de prompt/MCP funcionou na infra real, simular uma conversa de cliente, ou debugar roteamento/handoff/transferência ao vivo. Gatilhos PT-BR: 'testar o bot no webchat', 'testar via webchat', 'conversar com a IA ao vivo', 'mandar mensagem pro agente', 'validar o atendente no webchat', 'rodar um teste no webchat', 'o bot respondeu certo?', 'testa o agente publicado'. EN: 'test the nextags bot via webchat', 'drive the live webchat', 'talk to the deployed agent'. Diferente de simular o prompt em contexto: aqui passa pelo NexTags + MCP + backend de verdade (pega erro de credencial de MCP, payload grande, renderização de card, handoff entre agentes, transferência fantasma)."
metadata:
  type: reference
---

# NexTags Webchat Tester

Conversa com um agente de webchat **NexTags** (white-label da plataforma **tapthetable**) **ao vivo**, via WebSocket, direto do Python. Testa o agente **realmente publicado** end-to-end: modelo do NexTags → MCP → APIs de backend (Nuvemshop, Bling, Shopify, etc.).

## Quando usar

- O usuário quer confirmar que uma mudança de **prompt** ou de **MCP** funcionou **na infra real** (não só na simulação em contexto).
- Testar **roteamento/handoff** entre agentes, **transferência** (e detectar "transferência fantasma" = texto sem `send_flow`), interpretação de status, contratipo, etc.
- Reproduzir uma conversa de cliente que deu errado.

> **Por que não simular em contexto?** A simulação ("eu atuo como o bot dado o prompt") usa dados de tool FALSOS e pula a camada de backend/Meta. O teste real pega coisas que a simulação nunca pega: **credencial de MCP quebrada**, payload grande que trava a resposta, card que não renderiza, handoff que não dispara, etc.

## Pré-requisitos

1. `pip install websocket-client`
2. O **`page_id`**: é o `?p=<id>` da URL do webchat. Ex.: `https://app.nextagsai.com.br/webchat/?p=123456` → `page_id = 123456`. Peça ao usuário a URL do webchat se não souber.
3. Host do painel (default `https://app.nextagsai.com.br`). Se for outro white-label, ajuste `BASE` no script.

## Uso rápido

```bash
python scripts/webchat_test.py <page_id> "primeira mensagem" ["segunda mensagem" ...]
```

- Cada mensagem extra vai **em sequência na MESMA conversa** (1 contato novo).
- Para testar **cenários isolados** (resetar contexto e CUFs de roteamento como `agente_setor`), **rode o script várias vezes** — cada execução cria um contato novo.

Exemplos:
```bash
# saudação de entrada
python scripts/webchat_test.py <PAGE_ID> "oi"
# uma pergunta que exige o MCP (produto/pedido)
python scripts/webchat_test.py <PAGE_ID> "vocês têm tal produto?"
# handoff: a 1a msg cai num agente, a 2a deve trocar de agente
python scripts/webchat_test.py <PAGE_ID> "tenho um problema com meu pedido" "na verdade quero comprar outra coisa"
```

Para uma bateria de cenários, edite o `__main__` do script (ou escreva um wrapper) chamando `conversa([...])` por cenário.

## Protocolo (caso o script precise ser adaptado/reconstruído)

A página `/webchat/` é um app Vue que fala por **WebSocket**. Sequência:

1. **wsurl** — `POST {BASE}/php/user.php` com body `param=<json>` onde json = `{"op":"wt","account_id":<page_id>}`. Resposta: `data.wsurl` (ex.: `wss://ws.tapthetable.io/chat`). *(Buscar dinamicamente — não hardcodar.)*
2. **(opcional) config da página** — `POST {BASE}/php/no_login.php` param `{"op":"webChat","op1":"config","op2":"get","page_id":<page_id>}` → nome da loja, cor, etc.
3. **createUser** — `POST {BASE}/php/no_login.php` param `{"config_id":null,"page_id":<page_id>,"op":"webChat","op1":"createUser","data":{"timezoneOffset":-3,"timezoneName":"America/Sao_Paulo"}}` → `{ms_id, hash}`.
4. **conectar** no `wsurl` com header `Origin: {BASE}`.
5. **handshake** — enviar `{"action":-1,"data":{"dir":1,"sentBy":ms_id,"channel":9,"page_id":<page_id>,"ms_id":ms_id,"hash":hash}}`. Aguardar ~1s.
6. **enviar mensagem** — `{"action":0,"webchat":true,"data":{"dir":1,"sentBy":ms_id,"channel":9,"page_id":<page_id>,"ms_id":ms_id,"hash":hash,"liveChat":false,"timestamp":<ms>,"message":[{"text":"...","dir":1,"channel":9}]}}`.
7. **ler respostas** — frames do WS: `JSON.parse(frame).data.message[]` traz `text` e/ou `attachment` (type `image` | `template`/card). `dir`: 1 = cliente, 0 = bot.
8. **fallback de leitura por HTTP** (se o push do WS engasgar): `POST {BASE}/php/no_login.php` param `{"page_id":<page_id>,"ms_id":ms_id,"hash":hash,"op":"webChat","op1":"conversation","op2":"get","minMessageTime":0,"data":{...}}` → `data[]` mensagens guardadas (cada `.message` é string JSON; faça `JSON.parse`).

`channel` é sempre **9** (webchat). O webchat é **público** (sem login/token).

## Gotchas (aprendidos na marra)

- **Ping keepalive obrigatório:** respostas que chamam MCP demoram (10–40s) e o servidor **derruba a conexão ociosa** no meio. Mande `ws.ping()` a cada ~6s enquanto espera. (O script já faz.)
- **Janela de espera generosa:** respostas com tool/card podem levar 30–60s. Use `espera=45..75`.
- **"Kickstarter":** se NADA volta (0 frames e `getConversation` só com a sua mensagem), provavelmente o **agente não está sendo acionado** (gatilho/welcome desligado no NexTags). Não é o seu código — peça pro usuário conferir o acionamento do agente.
- **Cada conversa = contato novo:** `createUser` por conversa reseta contexto e CUFs (ex.: `agente_setor` que controla roteamento). Misturar cenários no mesmo contato contamina o teste.
- **send_flow não aparece nos frames:** a ação `send_flow` é executada no servidor; você **não** vê o action no WS. O sinal de que um **handoff/transferência disparou** é uma mensagem com o **texto característico do OUTRO agente/fluxo** aparecendo na sequência (ex.: a Maya respondendo num fluxo iniciado pela Lara). Use isso pra confirmar que a transferência foi REAL e não "fantasma" (texto "vou te passar" sem o agente novo assumir).
- **Não dispare transferências pra HUMANO em teste:** flows de atendente humano criam **ticket real** na fila. Teste handoffs entre IAs (que só trocam de fluxo) e evite os gatilhos de humano/financeiro.
- **Ordem dos frames pode interleaving:** mensagens próximas chegam quase juntas e podem sair fora de ordem no log; julgue pelo conteúdo, não pela ordem exata.

## Como interpretar o resultado

- `BOT[text]` = mensagem de texto. `BOT[image]` = imagem (confira a URL real do backend, ex.: `acdn-us.mitiendanube.com/...`). `BOT[card]` = template/botão (texto + URL do botão).
- **Card com imagem/preço/link reais do backend** = o MCP respondeu de verdade (não foi "decorado" do prompt).
- **Saudação do agente errado** (ex.: SAC respondendo pergunta de venda) = problema de **roteamento** (config do NexTags, ex.: CUF `agente_setor`).
- **"vou te passar..." e nenhum agente novo assume** = **transferência fantasma** (o prompt anunciou transferência sem emitir o `send_flow`).

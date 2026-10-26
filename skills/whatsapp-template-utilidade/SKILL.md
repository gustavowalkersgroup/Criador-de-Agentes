---
name: whatsapp-template-utilidade
description: "Criar e cadastrar modelos (templates) de WhatsApp no WhatsApp Manager da Meta na categoria Utilidade (coringa, carrinho, PIX, reativação, transacionais e disparos). Use ao cadastrar, variar ou analisar templates e ao entender por que a Meta reclassificou um modelo para Marketing."
---

# Templates WhatsApp aprovados como Utilidade (método Walkers)

Base: modelos aprovados e reclassificados lidos em contas de clientes NexTags, testes internos e lotes de out/2026. Idioma sempre Portuguese (BR). Versão 2: será refinada conforme chegarem mais modelos aprovados.

## Regra central
A Meta decide a categoria olhando principalmente (1) o texto fixo do corpo e (2) os EXEMPLOS das variáveis. Por isso:
- Texto fixo curto e neutro: saudação, variáveis, assinatura. Sem palavras comerciais (oferta, desconto, ganhou, cashback, confira, compre, quer ver?).
- As variáveis carregam o conteúdo (frases inteiras são aceitas no formato coringa).
- Os exemplos têm cara de aviso de conta, pedido, cadastro, rastreio ou agendamento.
- Exemplos com linguagem comercial ou genéricos ('nome', 'mensagem') levam à reclassificação para Marketing.

## Formato obrigatório do coringa (aprendido na prática)
1. CADA VARIÁVEL EM SUA PRÓPRIA LINHA, com linha em branco entre os blocos. Nunca colar {{1}} {{2}} {{3}} na mesma linha. Modelo:
```
Olá {{1}}, tudo bem?

{{2}}

{{3}}

Atenciosamente, equipe NomeDaEmpresa
```
2. RODAPÉ SEMPRE PREENCHIDO no padrão `Empresa | Digite STOP para sair` (STOP sempre em maiúsculas; empresa | opt-out; **máx. 60 caracteres**, `help.nextags.com.br/tutoriais/disparos/criar-modelo`). O rodapé conta para a proporção texto/variáveis, então ajuda a aprovar mais variáveis com menos texto fixo.
3. Se aparecer o erro 'Esse modelo contém muitas variáveis para sua extensão' (o botão Enviar para análise fica desabilitado): corpo curto com 3 variáveis + rodapé de 33 caracteres ainda foi recusado. Resolveu ao acrescentar uma frase neutra de abertura em linha própria, com cerca de 46 caracteres ou mais, por exemplo 'Segue uma atualização sobre o seu atendimento.' Frases usadas e aceitas: 'Temos uma atualização sobre o seu atendimento.', 'Aqui está uma atualização sobre o seu atendimento.', 'Segue uma informação sobre o seu atendimento conosco.' Frases com menos de 45 caracteres são arriscadas.
4. O formato acima começa e termina com texto, e isso é obrigatório: variável no início ou no fim do corpo é recusada (`help.nextags.com.br/tutoriais/disparos/modelo-reprovado`). Depois da última variável precisa vir texto fixo; uma frase de fechamento é o seguro. Confirmado em produção (26/10/2026): o padrão "pedido enviado" terminando em `{{4}}` não passou.
5. Ao definir o texto por script, usar '\n' real no setter nativo do textarea para criar as quebras. Conferir a prévia à direita: cada variável deve aparecer em um parágrafo separado.

## Padrões que passaram (Utilidade, com entregas reais)
| Tipo | Texto fixo | Exemplos | Botão |
|---|---|---|---|
| Transacional real (pedido enviado) | 'Seu pedido {{2}} foi enviado e já está em transporte. Código: {{3}}. Prazo: {{4}}. Qualquer dúvida, é só responder por aqui.' | Ana Paula / #57275 / NL123456789BR / 5 dias | Rastrear Pedido + Preciso de Ajuda |
| Pedido aprovado com confirmação | 'Parabéns! O seu pedido {{1}} foi aprovado. Você confirma esse pedido feito por {{2}}?' | X2645 / nome / rodapé com a marca | Confirmar + Preciso de Ajuda |
| Coringa | 'Olá {{1}}, tudo bem?' + frase neutra + {{2}} + {{3}} + 'Atenciosamente, equipe X' (cada variável em linha própria, ver formato obrigatório) | aviso de entrega ('Seu produto saiu para entrega'), pedido enviado, cadastro confirmado, agendamento, pagamento aprovado | Continuar, Ver detalhes ou Entendi |
| Carrinho | 'Atualização sobre {{2}}. O {{3}}. Clique no botão abaixo para receber' | aviso de cadastro/agendamento (SNS, exame agendado) | Continuar ou Pagar agora |
| PIX | 'Seu pedido de {{2}} {{3}} Clique no botão abaixo para receber o código' | 'pedido aprovado e será enviado' + endereço | PIX copia-e-cola |
| Reativação/confirmação | 'Um tempo atrás você realizou {{2}}. Falamos com {{3}} neste telefone?' | 'um cadastro no nosso sistema' / nome completo | Sim + Não |

Capa com imagem ou vídeo não muda a categoria. Rodapé com 'Digite STOP para sair' ou 'MARCA | BRASIL' não impediu aprovação. Os primeiros coringas (sem rodapé e sem quebras) foram aprovados como Utilidade, mas o formato correto é o da seção acima.

## O que foi reclassificado para Marketing (evitar)
- Exemplo com conteúdo de oferta: 'jeito lindo de completar esse look, e você ganhou R$ de cashback'.
- Fixo com convite comercial: 'Quer ver as sugestões?', 'Toque no botão abaixo e confere qual é', 'saber mais'.
- Exemplos vazios ou genéricos ('nome', 'mensagem') e fixo só com 'Aguardo seu retorno'.

## Cadastro no WhatsApp Manager (passo a passo)
1. Confirmar no cabeçalho da página qual conta está aberta  antes de qualquer coisa. NÃO abrir nova aba para a lista de modelos: a aba nova abriu outra conta de outro cliente por padrão. Trabalhar sempre na aba do usuário.
2. Modelos de mensagens > Criar modelo > aba Utilidade > tipo Padrão > Avançar.
3. Nome: minúsculas com underline, prefixo wl_ e sufixo de versão (wl_tipo_v2, v3...). Para imagem, wl_tipo_img_vN. Idioma: abrir o seletor, digitar 'Portuguese' e escolher Portuguese (BR) (a primeira opção; a segunda é PT).
4. Amostra de mídia: Nenhum, Imagem ou Vídeo. Para imagem: escolher Imagem no seletor, localizar o input de arquivo com a ferramenta de busca (find) e enviar com file_upload usando o ref retornado. Não clicar no botão de upload. O ref muda a cada formulário novo, então buscar de novo a cada modelo. O arquivo precisa estar no diretório de trabalho do Claude (ex.: /home/claude/arquivo.jpg); caminhos em /mnt/user-data/outputs foram recusados pelo navegador. JPG para imagem (1200x628 funciona); MP4 H.264/AAC curto para vídeo. Se o usuário não tiver imagem de capa, gerar uma simples com o nome da marca e avisar.
5. Corpo: o editor duplica chaves ao digitar {{1}} (vira {{1}}1}}). Definir o texto por script, usando o setter nativo do textarea e disparando os eventos input e change. Fazer o mesmo para exemplos e rodapé. Os inputs de exemplo têm placeholder 'Insira conteúdo para {{N}}' (os que já vêm com '{{N}}' são só rótulos); o rodapé tem placeholder 'Adicione uma pequena linha de texto à parte inferior'.
6. Exemplos: um por variável, sempre diferentes entre as versões (pedido enviado, rastreio X54646, entregue, pagamento aprovado, cadastro aprovado, agendamento).
7. Rodapé: sempre `Empresa | Digite STOP para sair`.
8. Botão: Adicionar botão > Personalizado > trocar 'Quick Reply' pelo texto (Continuar, Ver detalhes, Entendi...).
9. Validade da mensagem: deixar desligada, salvo pedido contrário.
10. Antes de enviar, ler os valores do formulário (nome, corpo, exemplos, rodapé, botão) e confirmar que o botão 'Enviar para análise' não está desabilitado (aria-disabled).
11. Enviar para análise. O envio demora de 20 a 40 segundos (spinner no botão) e depois volta sozinho para a lista com o aviso 'Seu modelo de mensagem foi enviado para análise'. Esperar, não reenviar. Se aparecer 'A categoria não corresponde', MANTER Utilidade selecionada e clicar Continuar (nunca trocar para Marketing sem ordem).
12. Se a Meta reclassificar para Marketing, o prazo para contestar a categoria é de **60 dias**, pelo Gerenciador do WhatsApp ou pelo suporte da Meta para empresas (`help.nextags.com.br/tutoriais/disparos/modelo-reprovado`). A revisão de uma recusa precisa de amostra (exemplos das variáveis e da mídia) e a Meta decide em até 24 horas. O responsável pela conta pede.
13. Se a extensão do navegador falhar no meio do envio, conferir na lista (por script, lendo as linhas da tabela) se o modelo foi criado antes de refazer, para não duplicar.
14. A página pode estar em modo 'Editar modelo' de um modelo existente: descartar só se ficar claro que não há alterações; o aviso diz que o progresso será perdido.

## Alternativa: criar pela NexTags
O modelo também se cria na NexTags: Configurações › Canais › WhatsApp › Configurações › aba **Modelo de Mensagem** › Adicionar; depois **Sincronizar** traz da Meta o que foi criado lá e o estado de cada um. Limites da tela: nome só com minúsculas, números e sublinhado; idioma **Portuguese (BR)**; corpo ≤1.024 caracteres; título ≤60 (no máximo 1 variável); rodapé ≤60; rótulo de botão ≤25 (até 10 botões no tipo Texto, até 3 nos de mídia e Localização; a Meta aceita até 2 de link e 1 de ligar); mídia ≤25 MB; a Meta responde em até 24 horas. Tipos de autenticação e de oferta por tempo limitado só se criam no Gerenciador do WhatsApp. A NexTags não edita modelo: corrigir é na Meta. Fontes: `help.nextags.com.br/tutoriais/disparos/criar-modelo`, `/o-que-e-um-modelo`.
Não há endpoint da API para criar modelo de WhatsApp (skill `nextags-api`). Não confundir com **Templates** de Ferramentas (copiar fluxos entre contas; `POST /accounts/templates/{id}/install`), que não são modelos do WhatsApp.

## Lotes de teste
Quando pedido um lote, gerar variações sutis do mesmo modelo (nome v2, v3...), mudando exemplos, saudação ('Olá' / 'Olá,'), frase neutra de abertura e texto do botão. Padrão: 3 sem mídia, 3 com imagem, 3 com vídeo, ou a quantidade pedida (ex.: 5 sem imagem e 5 com imagem). Todos já no formato obrigatório (variáveis em linhas separadas e rodapé). Cada modelo leva um fluxo completo de ações encadeadas; conferir o estado do formulário no retorno do script antes de enviar. Modelos antigos fora do formato não são apagados pelo Claude: avisar o responsável pela conta para apagar no WhatsApp Manager.

## Riscos (avisar o responsável pela conta)
- Exemplo que não representa o envio real pode levar a reclassificação posterior, queda de qualidade do número e restrição da conta (já houve restrição de 30 dias em outro cliente).
- Mensagem de pós-venda ('seu pedido foi aprovado') enviada com pagamento ainda pendente pode confundir o cliente e gerar bloqueios.
- Modelo aprovado ainda pode ser pausado pela nota de qualidade (bloqueios, denúncias, pouca leitura): 1ª vez 3 horas, 2ª 6 horas, 3ª desativa. Enquanto pausado não é enviado: pare os fluxos e Broadcasts que o usam (`help.nextags.com.br/tutoriais/disparos/modelo-reprovado`).
- Não alterar nem enviar nada em conta de cliente sem pedido explícito; ler o editor e sair sem salvar.
- Exemplos com nomes e números de pedido fictícios: avisar que precisam representar o uso real.

## Integração com as outras skills
- Disparos transacionais pelo webhook (pedido, rastreio, PIX): quem monta o endpoint é `nextags-webhook-builder`; esta skill cuida só do modelo aprovado na Meta.
- Fora da janela de 24 h o modelo só sai por um fluxo que **comece** com ele (etapa WhatsApp › Template Meta); pela API, `POST /contacts/{contact_id}/send/{flow_id}` (skill `nextags-api`). Modelo pausado, desativado ou não aprovado não é entregue.
- Custo: modelo de Utilidade enviado fora da janela de 24h é cobrado, e dentro da janela também passou a ser cobrado desde 01/10/2026. Para a conversa em si (mensagens de serviço do agente de IA), use `nextags-prompt-octobercut`.

## Fontes oficiais da NexTags

Antes de afirmar qualquer fato da plataforma (endpoint, limite, formato, canal, janela de 24 h), confira a fonte atual:
- API: skill `nextags-api` (`references/endpoints.md`, `live_shapes.md`), contrato oficial `docs.nextags.com.br/openapi.json`.
- Doc oficial (docs e help): MCP da documentação (`search`, `fetch`, `detalhar_endpoint`) ou o `.md` de cada página (troque a `/` final por `.md`); índices em `docs.nextags.com.br/llms.txt` e `help.nextags.com.br/llms.txt`.
- Se esta skill divergir da doc oficial, vale a doc: corrija a skill.

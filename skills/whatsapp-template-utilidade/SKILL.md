---
name: whatsapp-template-utilidade
description: "Criar e cadastrar modelos (templates) de WhatsApp no WhatsApp Manager da Meta na categoria Utilidade (coringa, carrinho, PIX, reativação, transacionais e disparos). Use ao cadastrar, variar ou analisar templates e ao entender por que a Meta reclassificou um modelo para Marketing."
---

# Templates WhatsApp aprovados como Utilidade (método Walkers)

Base: modelos aprovados e reclassificados lidos em contas de clientes NexTags, testes internos, lotes de out/2026, um lote de 20 coringas de um cliente e os testes de coringa enxuto de outro cliente (v11 a v22, out/2026). Idioma sempre Portuguese (BR). Versão 4 (31/out/2026): será refinada conforme chegarem mais modelos aprovados.

## Regra central
A Meta decide a categoria olhando principalmente (1) o texto fixo do corpo e (2) os EXEMPLOS das variáveis. Por isso:
- Texto fixo curto e neutro: saudação, variáveis, assinatura. Sem palavras comerciais (oferta, desconto, ganhou, cashback, confira, compre, quer ver?).
- As variáveis carregam o conteúdo (frases inteiras são aceitas no formato coringa).
- Os exemplos têm cara de aviso de conta, pedido, cadastro, rastreio ou agendamento.
- Exemplos com linguagem comercial ou genéricos ('nome', 'mensagem') levam à reclassificação para Marketing.

## Formato obrigatório do coringa (aprendido na prática)
1. CADA VARIÁVEL EM SUA PRÓPRIA LINHA, com linha em branco entre os blocos. Nunca colar {{1}} {{2}} {{3}} na mesma linha. Modelo padrão (com a chamada para o botão):
```
Olá {{1}}, tudo bem?

{{2}}

{{3}}

Clique no botão abaixo para saber mais!

Atenciosamente, equipe NomeDaEmpresa

[rodapé] Empresa | Digite STOP para sair
[botão] Ver detalhes
```
NÃO usar a frase de abertura de atendimento (ver item 5).
2. BOTÃO: TODO CORINGA LEVA 1 BOTÃO (Continuar, Ver detalhes ou Entendi). 'Só texto' significa sem mídia (sem imagem e sem vídeo), NÃO sem botão. No disparo da NexTags o fluxo só continua se o contato clicar em um botão, então coringa sem botão é inútil. Não interpretar 'não é pra ter mais coisas' como 'sem botão': isso se refere ao texto fixo. Na dúvida, perguntar sobre o botão antes de criar. Para o fluxo, lembrar que a saída 'Continuar' do modelo não pode ter mensagem ligada (dá erro de janela).
3. RODAPÉ SEMPRE PREENCHIDO no padrão `Empresa | Digite STOP para sair` (STOP sempre em maiúsculas; empresa | opt-out). O rodapé conta para a proporção texto/variáveis, mas NÃO precisa ser enchido com texto longo quando o corpo já tem a chamada 'Clique no botão abaixo...': o rodapé curto basta. LIMITE DO RODAPÉ: 60 caracteres (contador x/60 no formulário; `help.nextags.com.br/tutoriais/disparos/criar-modelo`). Com o nome da marca, 'Digite STOP para não receber mais nossas notificações' estourou (63); sem 'nossas' ficou com 56 e coube. Conferir o contador antes de enviar.
4. Se aparecer o erro 'Esse modelo contém muitas variáveis para sua extensão' (o botão Enviar para análise fica desabilitado): corpo curto com 3 variáveis + rodapé de 33 caracteres ainda foi recusado. Resolveu com a linha 'Clique no botão abaixo para saber mais!' (39 caracteres) antes da assinatura, que destravou o editor mesmo com o rodapé curto. Não resolver acrescentando a frase de abertura de atendimento (item 5, proibida).
5. FRASE DE ABERTURA DE ATENDIMENTO: PROIBIDA. Não usar 'Temos uma atualização sobre o seu atendimento.', 'Aqui está uma atualização sobre o seu atendimento.' nem variações ('atualização sobre o seu pedido', 'informação sobre o seu atendimento conosco'). Decisão do dono (nov/2026): não é possível usar. Histórico, só para entender o porquê: num lote de 20 coringas de um cliente (out/2026), as duas primeiras frases ficaram Utilidade e a 'informação ... conosco' foi reclassificada para Marketing 6 de 6; depois disso a frase de atendimento deixou de ser aceita como padrão. Se o usuário pedir essa frase, avisar que está proibida e usar a chamada para o botão (item 7).
6. O formato acima começa e termina com texto, e isso é obrigatório: variável no início ou no fim do corpo é recusada (`help.nextags.com.br/tutoriais/disparos/modelo-reprovado`). Depois da última variável precisa vir texto fixo; uma frase de fechamento é o seguro. Confirmado em produção (26/10/2026): o padrão "pedido enviado" terminando em `{{4}}` não passou.
7. CHAMADA PARA O BOTÃO (padrão do coringa, decisão do dono): linha 'Clique no botão abaixo para saber mais!' antes de 'Atenciosamente', com 1 botão ('Ver detalhes', 'Continuar' ou 'Entendi'). Num cliente, wl_coringa_txt_v21 (rodapé de 56 caracteres) e v22 (rodapé curto), mesmo corpo, mesmos exemplos e botão 'Ver detalhes', entraram como Utilidade em análise em 31/out/2026; o resultado final ainda precisa ser confirmado e esta regra atualizada. Risco conhecido: 'saber mais' já foi reclassificado para Marketing em outras contas. Se algum virar Marketing, testar 'Clique no botão abaixo para continuar.' ou 'Clique no botão abaixo para ver os detalhes.' (o padrão de Carrinho 'Clique no botão abaixo para receber' passou como Utilidade). Nunca voltar para a frase de atendimento.
8. NÃO USAR o coringa enxuto só com saudação + variáveis + assinatura (sem a chamada para o botão). O editor bloqueia por excesso de variáveis; aumentar a saudação ('Olá {{1}}, tudo bem? Esperamos que esteja tudo certo.') passa no editor, mas num cliente todos os modelos desse formato que ficaram visíveis (v11, v13, v15 e v16 a v20, com ou sem botão, 'Olá' ou 'Oi', saudação curta ou longa) foram reclassificados para Marketing em minutos ou horas. Os dois com 'Oi' (v12 e v14) sumiram da lista.
9. Ao definir o texto por script, usar '\n' real no setter nativo do textarea para criar as quebras. Conferir a prévia à direita: cada variável deve aparecer em um parágrafo separado.

## Padrões que passaram (Utilidade, com entregas reais)
| Tipo | Texto fixo | Exemplos | Botão |
|---|---|---|---|
| Transacional real (pedido enviado) | 'Seu pedido {{2}} foi enviado e já está em transporte. Código: {{3}}. Prazo: {{4}}. Qualquer dúvida, é só responder por aqui.' | Ana Paula / #57275 / NL123456789BR / 5 dias | Rastrear Pedido + Preciso de Ajuda |
| Pedido aprovado com confirmação | 'Parabéns! O seu pedido {{1}} foi aprovado. Você confirma esse pedido feito por {{2}}?' | X2645 / nome / rodapé com a marca | Confirmar + Preciso de Ajuda |
| Transacional com 1 botão (pedido enviado, aprovado, em transporte, entregue, pagamento aprovado) | 'Olá {{1}}, tudo bem?' + aviso do pedido/pagamento em linhas próprias + 'Atenciosamente, equipe X' | nome, número do pedido, rastreio, prazo, valor | Preciso de ajuda (1 botão); as versões com 2 botões (Continuar ou Ok + Preciso de ajuda) também ficaram Utilidade |
| Coringa com chamada para o botão (padrão) | 'Olá {{1}}, tudo bem?' + {{2}} + {{3}} + 'Clique no botão abaixo para saber mais!' + 'Atenciosamente, equipe X' (cada variável em linha própria, ver formato obrigatório) | aviso de entrega ('Seu produto saiu para entrega'), pedido enviado, cadastro confirmado, agendamento, pagamento aprovado | Ver detalhes, Continuar ou Entendi |
| Carrinho | 'Atualização sobre {{2}}. O {{3}}. Clique no botão abaixo para receber' | aviso de cadastro/agendamento (SNS, exame agendado) | Continuar ou Pagar agora |
| PIX | 'Seu pedido de {{2}} {{3}} Clique no botão abaixo para receber o código' | 'pedido aprovado e será enviado' + endereço | PIX copia-e-cola |
| Reativação/confirmação | 'Um tempo atrás você realizou {{2}}. Falamos com {{3}} neste telefone?' | 'um cadastro no nosso sistema' / nome completo | Sim + Não |

Capa com imagem ou vídeo não muda a categoria. Rodapé com 'Digite STOP para sair' ou 'MARCA | BRASIL' não impediu aprovação. Os primeiros coringas (sem rodapé e sem quebras) foram aprovados como Utilidade, mas o formato correto é o da seção acima.

## O que foi reclassificado para Marketing (evitar)
- Exemplo com conteúdo de oferta: 'jeito lindo de completar esse look, e você ganhou R$ de cashback'.
- Fixo com convite comercial: 'Quer ver as sugestões?', 'Toque no botão abaixo e confere qual é', 'saber mais' solto (a exceção é a chamada padrão 'Clique no botão abaixo para saber mais!', item 7).
- Exemplos vazios ou genéricos ('nome', 'mensagem') e fixo só com 'Aguardo seu retorno'.
- Coringa com a frase de abertura 'Segue uma informação sobre o seu atendimento conosco.' (6 de 6 num lote de um cliente). As frases 'Temos/Aqui está uma atualização sobre o seu atendimento.' estão proibidas (item 5).
- Coringa enxuto só com saudação + variáveis + assinatura, mesmo com saudação aumentada e botão (v11 a v20 de um cliente).
- Modelo APROVADO editado para acrescentar botão: voltou para análise e foi reclassificado (v11, v13 e v15 estavam em Utilidade ativos e viraram Marketing em análise). Para mudar um modelo bom, criar nova versão e deixar o antigo intacto.

## Cadastro no WhatsApp Manager (passo a passo)
1. Confirmar no cabeçalho da página qual conta está aberta antes de qualquer coisa. NÃO abrir nova aba para a lista de modelos e NÃO navegar por endereço direto (navigate para a URL de message_templates): a aba nova abriu outra conta e o endereço direto abriu a conta de outro cliente, ambos por padrão. Para voltar à lista ou reler status, clicar em 'Gerenciar modelos' no menu lateral ou usar navigate 'back'. Trabalhar sempre na aba do usuário. Se as ações do navegador começarem a falhar ou as coordenadas não baterem, tirar um screenshot: a janela pode ter encolhido ou mudado de tamanho (resize_window para 1296x924 e recalibrar as coordenadas; as coordenadas do seletor de idioma mudam com o tamanho da janela, então calibrar com um screenshot).
2. Modelos de mensagens > Criar modelo > aba Utilidade > tipo Padrão > Avançar. CONFERIR A CATEGORIA: depois de Avançar, o cabeçalho do formulário deve mostrar 'Utilidade · Padrão'. Um clique por script na aba 'Utilidade' falhou sem avisar e o formulário abriu como Marketing (por isso usar clique real na aba Utilidade e conferir no screenshot antes de Avançar). Se abrir como Marketing, clicar em Voltar e, no aviso 'As alterações serão perdidas', em Voltar de novo (descarta só o rascunho, nada foi enviado), e refazer.
3. Nome: minúsculas com underline, prefixo wl_ e sufixo de versão (wl_tipo_v2, v3...). Para imagem, wl_tipo_img_vN; para vídeo, wl_tipo_vid_vN. Idioma: abrir o seletor, digitar 'Portuguese' e escolher Portuguese (BR) (a primeira opção; a segunda é PT). O NOME DEVE SER DIGITADO COM TECLAS REAIS (clicar no campo ou dar focus() por script e usar type), nunca só pelo setter de script: com o nome definido por script o botão 'Enviar para análise' ficou desabilitado e o título do cabeçalho continuou 'your_template_name'. Corpo, exemplos, rodapé e botão podem ser definidos por script. Ao conferir o idioma por script, o cabeçalho usa '•' (ex.: 'wl_x • Portuguese (BR)'), aceitar '•' ou '·' na checagem.
4. Amostra de mídia: Nenhum, Imagem ou Vídeo. Para imagem/vídeo: escolher no seletor, localizar o input de arquivo com a ferramenta de busca (find) e enviar com file_upload usando o ref retornado (file_upload funciona dentro do browser_batch). Não clicar no botão de upload. O ref muda a cada formulário novo, então buscar de novo a cada modelo (um find no fim de uma chamada, o file_upload no começo da seguinte). O arquivo precisa estar no diretório de trabalho do Claude (ex.: /home/claude/arquivo.jpg); caminhos em /mnt/user-data/outputs foram recusados pelo navegador. JPG para imagem (1200x628 funciona); MP4 H.264/AAC curto para vídeo (5 s foi aceito). Se o usuário não tiver imagem de capa, gerar uma simples com o nome da marca e avisar. Conferir que a prévia mostra a mídia antes de enviar.
5. Corpo: o editor duplica chaves ao digitar {{1}} (vira {{1}}1}}). Definir o texto por script, usando o setter nativo do textarea e disparando os eventos input e change. Fazer o mesmo para exemplos e rodapé. Os inputs de exemplo têm placeholder 'Insira conteúdo para {{N}}' (os que já vêm com '{{N}}' são só rótulos); o rodapé tem placeholder 'Adicione uma pequena linha de texto à parte inferior'.
6. Exemplos: um por variável, sempre diferentes entre as versões (pedido enviado, rastreio X54646, entregue, pagamento aprovado, cadastro aprovado, agendamento). Exceção: em teste A/B de uma única variável (ex.: só o rodapé), manter os mesmos exemplos nos dois modelos para a comparação ser limpa, e avisar o responsável pela conta.
7. Rodapé: sempre `Empresa | Digite STOP para sair`, no máximo 60 caracteres.
8. Botão (obrigatório no coringa): Adicionar botão > Personalizado > trocar 'Quick Reply' pelo texto (Continuar, Ver detalhes, Entendi...). Por script funciona: clicar em 'Adicionar botão', depois no item 'Personalizado' (por texto), e definir o input que vale 'Quick Reply'. Antes de enviar, conferir que existe exatamente 1 input com o texto do botão e que a prévia mostra o botão.
9. Validade da mensagem: deixar desligada, salvo pedido contrário.
10. Antes de enviar, ler os valores do formulário (nome, categoria, idioma, corpo, exemplos, rodapé e seu tamanho, botão) e confirmar que o botão 'Enviar para análise' não está desabilitado (aria-disabled) e que não há o erro de muitas variáveis. Se estiver desabilitado, rever primeiro o nome (item 3) e a chamada para o botão (regra 4). Abortar a cadeia, sem enviar, se algo estiver errado.
11. Enviar para análise. O envio demora de 20 a 40 segundos (spinner no botão) e depois volta sozinho para a lista com o aviso 'Seu modelo de mensagem foi enviado para análise'. Esperar, não reenviar. Se aparecer 'A categoria não corresponde', MANTER Utilidade selecionada e clicar Continuar (nunca trocar para Marketing sem ordem). Esse aviso aparece em praticamente todo envio e recomenda Marketing; é esperado.
12. Se a Meta reclassificar para Marketing, o prazo para contestar a categoria é de **60 dias**, pelo Gerenciador do WhatsApp ou pelo suporte da Meta para empresas (`help.nextags.com.br/tutoriais/disparos/modelo-reprovado`). A revisão de uma recusa precisa de amostra (exemplos das variáveis e da mídia) e a Meta decide em até 24 horas. O responsável pela conta pede. A reclassificação pode vir em cerca de 3 minutos ou só horas depois do envio: reler a lista de status após o lote e refazer os reprovados com ajuste de texto, em novas versões, sem apagar os antigos. Modelo já aprovado que o usuário queira mudar: criar nova versão em vez de editar o existente (editar manda de volta para análise e pode perder a categoria).
13. Se a extensão do navegador falhar no meio do envio, conferir na lista (por script, lendo as linhas da tabela; se a tela travar, voltar à lista pelo menu lateral) se o modelo foi criado antes de refazer, para não duplicar. Chamadas de script com espera de mais de cerca de 40 segundos falham na extensão: dividir esperas longas em várias chamadas. Um script que termina navegando pode retornar 'undefined': reler o estado da página em vez de repetir a ação.
14. A página pode estar em modo 'Editar modelo' de um modelo existente: descartar só se ficar claro que não há alterações; o aviso diz que o progresso será perdido. Na tela de edição existe o botão 'Excluir modelo': nunca clicar.
15. A lista de modelos carrega aos poucos: rolar a página e os contêineres até o fim para ler todas as linhas. Para saber o número de botões de um modelo, abrir o detalhe (a seção 'Seu modelo' mostra o corpo, o rodapé e os botões).

## Alternativa: criar pela NexTags
O modelo também se cria na NexTags: Configurações › Canais › WhatsApp › Configurações › aba **Modelo de Mensagem** › Adicionar; depois **Sincronizar** traz da Meta o que foi criado lá e o estado de cada um. Limites da tela: nome só com minúsculas, números e sublinhado; idioma **Portuguese (BR)**; corpo ≤1.024 caracteres; título ≤60 (no máximo 1 variável); rodapé ≤60; rótulo de botão ≤25 (até 10 botões no tipo Texto, até 3 nos de mídia e Localização; a Meta aceita até 2 de link e 1 de ligar); mídia ≤25 MB; a Meta responde em até 24 horas. Tipos de autenticação e de oferta por tempo limitado só se criam no Gerenciador do WhatsApp. A NexTags não edita modelo: corrigir é na Meta. Fontes: `help.nextags.com.br/tutoriais/disparos/criar-modelo`, `/o-que-e-um-modelo`.
Não há endpoint da API para criar modelo de WhatsApp (skill `nextags-api`). Não confundir com **Templates** de Ferramentas (copiar fluxos entre contas; `POST /accounts/templates/{id}/install`), que não são modelos do WhatsApp.

## Lotes de teste
Quando pedido um lote, gerar variações sutis do mesmo modelo (nome v2, v3...), mudando exemplos, saudação ('Olá' / 'Olá,') e texto do botão, e alternando o texto do botão ('Ver detalhes', 'Continuar', 'Entendi'); a frase de abertura de atendimento é proibida (regra 5). Padrão: 3 sem mídia, 3 com imagem, 3 com vídeo, ou a quantidade pedida (ex.: 5 sem imagem e 5 com imagem). Todos já no formato obrigatório (variáveis em linhas separadas, rodapé e 1 botão). Preferir 'Olá' a 'Oi': num cliente os dois modelos com 'Oi' foram os que sumiram da lista (pista, não prova). Cada modelo leva um fluxo completo de ações encadeadas (abrir, Utilidade, Avançar, idioma, nome digitado, mídia, preenchimento por script, conferência, envio, espera); conferir o estado do formulário no retorno do script antes de enviar e abortar a cadeia se o botão estiver desabilitado.
FORMATO NOVO OU NÃO COMPROVADO: criar primeiro 1 ou 2 modelos, esperar cerca de 5 a 10 minutos pela primeira reclassificação e só então criar o resto do lote; mudar uma variável por vez (ex.: v21 e v22 só diferem no rodapé). Criar o lote inteiro de uma vez com um formato que acaba de falhar gera lixo no WhatsApp Manager (v11 a v20 de um cliente acabaram em Marketing).
Ao final, reler a lista e relatar quais ficaram como Utilidade e quais foram reclassificados. Modelos antigos fora do formato ou reprovados não são apagados pelo Claude: avisar o responsável pela conta para apagar no WhatsApp Manager, listando os nomes.

## Riscos (avisar o responsável pela conta)
- Exemplo que não representa o envio real pode levar a reclassificação posterior, queda de qualidade do número e restrição da conta (já houve restrição de 30 dias em outro cliente).
- Mensagem de pós-venda ('seu pedido foi aprovado') enviada com pagamento ainda pendente pode confundir o cliente e gerar bloqueios.
- Modelo aprovado ainda pode ser pausado pela nota de qualidade (bloqueios, denúncias, pouca leitura): 1ª vez 3 horas, 2ª 6 horas, 3ª desativa. Enquanto pausado não é enviado: pare os fluxos e Broadcasts que o usam (`help.nextags.com.br/tutoriais/disparos/modelo-reprovado`).
- Não alterar nem enviar nada em conta de cliente sem pedido explícito; ler o editor e sair sem salvar.
- Exemplos com nomes e números de pedido fictícios: avisar que precisam representar o uso real.
- Editar modelo aprovado coloca ele de volta em análise e ele fica indisponível para envio até a Meta responder, com risco de virar Marketing.

## Integração com as outras skills
- Disparos transacionais pelo webhook (pedido, rastreio, PIX): quem monta o endpoint é `nextags-webhook-builder`; esta skill cuida só do modelo aprovado na Meta.
- Fora da janela de 24 h o modelo só sai por um fluxo que **comece** com ele (etapa WhatsApp › Template Meta); pela API, `POST /contacts/{contact_id}/send/{flow_id}` (skill `nextags-api`). Modelo pausado, desativado ou não aprovado não é entregue.
- Custo: modelo de Utilidade enviado fora da janela de 24h é cobrado, e dentro da janela também passou a ser cobrado desde 01/10/2026. Para a conversa em si (mensagens de serviço do agente de IA), use `nextags-prompt-octobercut`.

## Fontes oficiais da NexTags

Antes de afirmar qualquer fato da plataforma (endpoint, limite, formato, canal, janela de 24 h), confira a fonte atual:
- API: skill `nextags-api` (`references/endpoints.md`, `live_shapes.md`), contrato oficial `docs.nextags.com.br/openapi.json`.
- Doc oficial (docs e help): MCP da documentação (`search`, `fetch`, `detalhar_endpoint`) ou o `.md` de cada página (troque a `/` final por `.md`); índices em `docs.nextags.com.br/llms.txt` e `help.nextags.com.br/llms.txt`.
- Se esta skill divergir da doc oficial, vale a doc: corrija a skill.

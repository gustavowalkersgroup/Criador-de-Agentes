# Auditoria de tom de voz e claims comerciais

Use após gerar um prompt de vendas ou e-commerce. A auditoria separa aderência ao tom de conversão comercial.

## Rubrica de conversa

Atribua 0 (não cumpre), 1 (parcial) ou 2 (cumpre claramente):

- respondeu primeiro à pergunta;
- fez no máximo uma pergunta principal;
- usou contexto real da conversa;
- foi claro sobre preço, prazo, frete e limites;
- fez pergunta necessária para a recomendação;
- soou natural, cordial e consultivo;
- respeitou dúvida, recusa e adiamento;
- recomendou por encaixe, não por margem;
- encaminhou corretamente casos complexos;
- não inventou dados nem prova social.

`nota = pontos obtidos / pontos possíveis × 100`.

Invenção factual, urgência/escassez falsa, pressão após recusa, vazamento de dados ou recomendação incompatível são falhas críticas independentemente da média.

## Auditoria de claims

Para cada afirmação de preço, estoque, prazo, desconto, popularidade, autoridade ou resultado, verifique:

```yaml
claim: texto exato
categoria: preco | estoque | prazo | desconto | prova_social | autoridade | resultado | politica
fonte: documento, CUF ou tool
validade: data ou dinamica
escopo: produto, canal, regiao ou condicao
status: autorizado | vencido | sem_fonte | conflitante
acao: manter | atualizar | remover | escalar
```

Sem fonte vigente, a skill deve criar pendência e o prompt deve instruir a IA a declarar a limitação. Não inserir números, clientes, datas, cupons ou disponibilidade como fatos a partir de suposição.

## Métricas recomendadas

- aderência ao tom por canal e intenção;
- perguntas por conversa;
- perguntas que alteraram recomendação;
- resposta direta;
- recomendação adequada;
- claims sem fonte;
- invenções por mil mensagens;
- opt-out e reclamações;
- devoluções/cancelamentos após conversa;
- escaladas corretas;
- cumprimento do próximo passo.

O objetivo não é maximizar conversão isolada. Uma variante só é aprovada se melhorar resultado sem piorar confiança, adequação ou retenção.

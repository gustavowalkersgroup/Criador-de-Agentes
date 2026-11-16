# Prompt-base Codex: mapear catálogo para matching por imagem

Adapte caminhos, índices e orçamento antes de usar.

> Inspecione os arquivos deste projeto relacionados ao catálogo. Preserve as entradas e crie backup antes de gerar saídas. Identifique inventário, resultados existentes, estrutura dos registros e IDs pendentes. Considere concluído somente o item que tenha payload analítico válido, não marcador de status. Não invente dados para resultados ausentes.
>
> Processe apenas os IDs pendentes definidos: **[INFORME IDs ou filtro]**. Faça lotes de 5 itens, com no máximo 8 após validar dois lotes. Para cada item, consulte a ficha oficial e use somente a primeira imagem principal. Não abra galeria nem pesquise variantes, salvo pedido expresso. Reutilize cache local e pule somente registros existentes com payload válido.
>
> Separe informação textual oficial de observação visual. Extraia tipo de produto, família/modelo, silhueta/forma, padrão/estampa, cor oficial, cores observadas e detalhes distintivos úteis à busca. Registre fontes e incertezas. Não infira material, composição, medidas, disponibilidade, fechos ou forro pela foto. Para artesanato, anote que cor/desenho pode variar. Se a visão não estiver disponível, marque isso claramente.
>
> Grave um JSONL de resultados, um JSONL de erros e um manifest de checkpoint; faça validação após cada lote. Não apague resultados válidos nem reescreva arquivos de origem. Em falhas, registre o item e avance; retente somente itens com falha transitória, no máximo duas vezes. Pare em bloqueios, CAPTCHA, login ou limite de créditos; não tente contorná-los.
>
> Antes de chamadas pagas/de alto custo, mostre plano, primeiro lote e custo/limites aplicáveis e aguarde minha confirmação. Comece inspecionando arquivos e criando backup/manifest; não processe itens até essa revisão. Ao final, compare IDs do inventário com resultados válidos, liste pendências/falhas e marque cobertura completa somente se todos os itens do escopo tiverem payload real. Gere um JSON consolidado e um resumo Markdown sem alegar busca por embeddings se ela não foi implementada.

# Entrevistador Digital V9.7.2 | Parecer aprofundado e aprovação em PDF

Esta atualização parte da V9.7 e **inclui a correção do botão de aprovação e geração do PDF da V9.7.1**. Não exige instalar novos pacotes nem alterar senha do Render.

## O que muda

- O texto da minuta de cliente deixa de mencionar importação, anexação ou extração de documentos.
- O histórico profissional e as respostas passam a ser relacionados às responsabilidades da vaga, hard skills e soft skills com parágrafos mais analíticos. A descrição permanece cautelosa: relatos não são convertidos em provas independentes de desempenho.
- Declarações de ausência de experiência são tratadas como lacunas específicas, e não como evidência favorável.
- Respostas repetidas não são contadas como demonstrações diferentes.
- O DISC permanece complementar e não atribui nota de competência técnica.
- **Aprovar e gerar dossiê PDF** salva as três seções e emite o arquivo em uma operação. Se a renderização falhar, a aprovação não fica registrada.
- **Preparar novamente o texto** cria uma nova proposta editorial sem sobrescrever automaticamente o parecer aprovado; o sistema pergunta antes de substituir os campos de edição.
- O PDF mantém as três seções oficiais e não revela metodologia de cálculo, pesos ou notas individuais.

## Instalação manual no GitHub + Render

1. Como o armazenamento do Render Free é efêmero, confira se o backup já baixado contém banco e arquivos antes do deploy. Guarde também os PDFs originais.
2. Extraia o ZIP e envie os arquivos nas mesmas pastas do repositório privado GitHub: `server.py`, `evidence_draft.py`, `client_report.py`, `static/index.html`, `static/app.js`, `static/interview.html`.
3. Faça commit na branch usada pelo Render (`main`, se essa for a branch cadastrada).
4. No Render, execute **Manual Deploy > Deploy latest commit**. Não mude variáveis ou senhas.
5. Confira `https://entrevistador-digital.onrender.com/api/health` e procure `9.7.2-editorial-review`.
6. Em **Entrevistas e dossiês**, selecione um candidato com respostas disponíveis e clique **Preparar novamente o texto a partir das fontes**. Revise as três seções, especialmente a recomendação.
7. Clique **Aprovar e gerar dossiê PDF**. O download será iniciado e a opção **Baixar parecer aprovado PDF** permanecerá disponível caso o navegador bloqueie o download automático.

## Limites de funcionamento

- Essa versão **não dispõe de interpretação semântica por um modelo de linguagem** no Render Free. A minuta usa critérios, trechos localizados e respostas existentes, portanto não deve ser apresentada como avaliação automática integral.
- O recrutador deve corrigir redação, confirmar fatos e definir a recomendação antes de aprovar.
- Se faltarem currículo, DISC, LinkedIn ou respostas, a minuta sinalizará as lacunas sem preencher fatos por suposição.
- O backup não substitui um armazenamento persistente; o serviço Free pode perder dados em reinicializações.
- Arquivos já aprovados permanecem intactos; gerar uma nova proposta editorial não os atualiza silenciosamente.

## Testes

Executar `pytest -q tests`. Os cenários cobrem geração de minuta, linguagem do PDF, ausência de jargão operacional, respostas curtas, negativas expressas, repetição, aprovar + exportar, permissões, senhas e backup.

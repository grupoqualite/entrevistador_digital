# Qualité Entrevistar Digital | Correção 9.7.7.2

## Base e abrangência

Atualização feita sobre o código 9.7.7.1, que por sua vez preserva a estrutura da versão funcional 9.7.5. **Não reinstale o serviço, não apague o banco e não recrie usuários.** O `static/index.html` do hotfix de login foi preservado. O mecanismo de verificação entre HTML e JavaScript continua exigindo o mesmo identificador compatível.

## O que mudou

1. **Parecer externo, três seções**: Competências Técnicas, Competências Comportamentais e Parecer de Recomendação. A redação sintetiza práticas, limites de experiência e relação com a vaga, sem copiar trechos literais do candidato. Citações e respostas permanecem na trilha **interna**, para auditoria do recrutador.
2. **Triagem preliminar de fontes**: o questionário, currículo, LinkedIn e apresentação profissional passam a ser examinados por requisito; DISC permanece como contextualização comportamental. A triagem por regras informa quais fontes apresentam referências relacionadas, **não atribui nota** e não se declara IA.
3. **IA × recrutador**: quando um modelo contextual local está realmente configurado, a avaliação preliminar por requisito considera currículo, LinkedIn, respostas, apresentação e DISC (este último somente para contextualização, sem nota). A tela interna apresenta nota do modelo, nota final, justificativa e concordância/divergência com a revisão humana. Se não houver modelo, registra expressamente “IA não avaliou”; o recrutador pode registrar nota independente sem fingir que foi homologada uma avaliação de IA.
4. **Critérios inválidos**: a expressão-padrão “Novo critério, inserir origem e competência” não entra no denominador nem no parecer. A exclusão é registrada na análise interna, para que a vaga possa ser revisada.
5. **Proteção do documento externo**: a aprovação e a exportação recusam pareceres com citações literais sinalizadas por aspas tipográficas; os relatórios anteriores devem ser reeditados/revisados.
6. **Identidade visual e login**: preservados. A marca da plataforma não substitui o logo escolhido para o PDF.

## Limite importante da IA

**No Render sem modelo Ollama ou outro servidor de modelos explicitamente configurado, não há avaliação generativa de IA.** O sistema consegue fazer a triagem documental e preparar uma minuta editorial conservadora, mas não pode atribuir notas e declarar que são provenientes de IA. Para confrontar de fato notas do modelo e do humano, será necessário disponibilizar um serviço de inferência autorizado, com segurança compatível com dados pessoais dos candidatos. Não é correto contratar ou conectar serviço externo sem autorização e avaliação de privacidade.

## Upload manual ao GitHub e deploy manual ao Render

1. Faça backup completo dos dados, anexos e banco. Guarde o backup privadamente fora do Render.
2. **Para o código 9.7.7.1 já implantado**, use o ZIP de **correção incremental**, atualizando somente os arquivos que ele contém, mantendo a mesma estrutura de pastas. Não substitua `static/index.html` e não toque no SQLite.
3. Se for reinstalar o código-fonte inteiro sobre uma cópia limpa da aplicação, use o **ZIP completo**. Não copie arquivos de banco ou segredos sobre os dados existentes.
4. No GitHub, faça commit na branch conectada ao Render. No Render, selecione *Manual Deploy → Deploy latest commit*.
5. Confira `https://entrevistador-digital.onrender.com/api/health`: o campo `build` deverá ser `qualite-parecer-analitico-confronto-9772`; o campo `version` permanece `9.7.7-parecer-qualite` para não quebrar a conferência de compatibilidade da interface.
6. Abra uma janela anônima. Confirme o login com as mesmas credenciais anteriores, selecione um candidato com as fontes cadastradas, execute a análise e abra o relatório interno. Verifique a triagem de fontes, notas do modelo (se configurado), notas do recrutador e divergências.
7. Gere a minuta, revise o texto das três seções, salve e aprove. Abra o PDF para conferir que não contém falas literais nem texto-padrão de perguntas e que o logo personalizado do cliente foi preservado.

## Cuidados em candidaturas existentes

A atualização não reprocessa nem modifica automaticamente pareceres que já foram editados ou aprovados. Um texto antigo com transcrições literais exige revisão e novo salvamento pelo recrutador antes de uma nova aprovação/exportação. Não substitua uma avaliação humana anterior silenciosamente.

## Verificações executadas

- Compilação Python e verificação sintática do JavaScript.
- 21 testes automatizados locais aprovados, incluindo autenticação, cinco fontes, revisão humana sem IA, integração simulada com modelo, critérios inválidos e PDF sem citações literais.
- PDF de exemplo fictício gerado e conferido visualmente.

**Não realizado:** deploy no Render do usuário, teste pelo navegador no ambiente de produção e execução com modelo Ollama real configurado. O teste de IA usa resposta simulada, que verifica fluxo e estrutura, não a qualidade de um modelo real.

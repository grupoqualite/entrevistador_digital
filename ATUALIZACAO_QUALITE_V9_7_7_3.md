# Qualité Entrevistar Digital | 9.7.7.3

Base: pacote completo 9.7.7.2. Atualização incremental de questionários.

## O que muda
- Ao incluir uma pergunta manual, a classificação inicia sem seleção. Escolha Hard Skill, Soft Skill, Diferencial ou Análise de responsabilidade. A opção Condições da vaga também é preservada.
- Informe um critério específico (competência, responsabilidade ou diferencial), a pergunta e o peso de 1 a 5. O servidor impede campos inválidos ou o antigo texto-padrão de critério. Nenhuma pergunta inválida é excluída silenciosamente.
- A classificação de questões geradas automaticamente também pode ser corrigida antes de emitir convites. Os campos de origem permanecem como referência à descrição da vaga.
- Diferencial tem natureza técnica, comportamental ou de responsabilidade; o seletor inicia em Hard Skill quando não existe uma natureza já definida. O diferencial continua fora do denominador de aderência essencial; sua nota é calculada separadamente. Condições da vaga continuam separadas da aderência técnica/comportamental.
- Não foi alterado o código de autenticação, armazenamento, geração de parecer ou integração com IA. A matriz existente consome a classificação persistida, sem migração de banco. Não há reclassificação automática das entrevistas existentes.
- Questionários com convites emitidos continuam bloqueados para edição, para preservar o vínculo entre perguntas e respostas. Para mudar o roteiro, crie uma nova vaga/versão. Antes de salvar um roteiro antigo ainda editável, complete eventuais critérios genéricos.

## Implantação manual
1. No sistema atual, faça backup completo dos dados e anexos. Verifique o ZIP e guarde fora do Render. A atualização não altera o armazenamento; reinicializações podem provocar perda de dados quando a pasta de dados for efêmera.
2. Use o pacote incremental somente sobre a versão 9.7.7.2. Extraia-o e substitua `server.py`, `static/app.js` e `static/index.html` juntos, no mesmo commit. O documento MD é opcional no repositório.
3. Se a versão em produção for anterior à 9.7.7.2, use o pacote completo, mantendo os dados e as configurações do ambiente. Não apague o banco nem altere as variáveis de senha.
4. No Render, execute Manual Deploy > Deploy latest commit. Abra em janela anônima. Em `/api/health`, confirme `build: qualite-questionarios-classificados-9773`. O campo `version` permanece `9.7.7-parecer-qualite` para compatibilidade entre HTML e JavaScript. O painel exibe V9.7.7.3 ao consultar o build.
5. Autentique-se com a senha atual. Em Vagas e roteiro, use uma vaga de teste ainda sem convites, inclua perguntas de cada classe, informe os critérios e salve. Reabra a mesma vaga e confira se classificação, natureza do diferencial, critério e peso permanecem corretos. Teste a avaliação em um candidato fictício antes de utilizar com candidatos reais.
6. Caso seja necessário reverter, restaure os três arquivos anteriores no GitHub e faça o deploy do commit anterior. Se ocorrer perda de dados por infraestrutura, use o backup verificado.

## Validação local
- 22 testes pytest aprovados: regressões existentes, autenticação, persistência de seis combinações, rejeição de classificação/critério inválido, cálculo por grupo e bloqueio após convite.
- Sintaxe do JavaScript e compilação do servidor verificadas.
- Navegação automatizada pelo Chromium bloqueada pela política do ambiente (`ERR_BLOCKED_BY_ADMINISTRATOR`); interface em navegador real e implantação no Render não homologadas aqui.
- Nenhuma alteração direta no GitHub/Render e nenhum dado real incluído no pacote.

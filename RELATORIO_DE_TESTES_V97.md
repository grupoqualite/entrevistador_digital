# Relatório de testes V9.7.0

Executados localmente em Python 3.13, FastAPI TestClient, sem chamadas a modelos externos:

- Cadastro de vaga e candidato com currículo e DISC fictícios.
- Entrevista com respostas por texto; conclusão cria minuta imediatamente.
- Prévia PDF das três seções antes da aprovação; indicação explícita de minuta.
- Bloqueio de PDF final sem revisão/aprovação.
- Salvamento, aprovação nominal, geração de PDF final e revogação da aprovação após edição.
- Entrevista histórica com áudio pendente, sem tentativa de transcrever ou simular conteúdo.
- Minuta cautelosa para respostas excessivamente curtas.
- Recuperação de relatório legado com histórico de revisão humana, preservando-o ao criar as seções externas ausentes.
- Regressão de autenticação, usuários, senhas, backups e entrevista somente por texto.
- Inspeção visual de PDF fictício renderizado via PDFium.

Resultado: **12 testes automatizados aprovados**. A sintaxe de `app.js` e `interview.js` foi conferida com Node.js. O navegador Chromium do ambiente bloqueou a navegação ao endereço de desenvolvimento local (`ERR_BLOCKED_BY_ADMINISTRATOR`); portanto, a navegação completa no serviço Render/iPhone **não está homologada nesta etapa**.

A geração documental não constitui validação de aderência técnica por modelo semântico. Notas automáticas continuam indisponíveis quando não há Ollama conectado.

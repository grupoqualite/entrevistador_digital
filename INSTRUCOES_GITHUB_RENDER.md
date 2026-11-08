# Entrevistador Digital V9.6.4 — Backup visível e senhas de usuários

## O que muda

- **Administrador:** encontra o botão **Restaurar backup ZIP** no topo do painel e também a aba **Backup e restauração**. Pode baixar e restaurar backups; a operação exige ZIP válido e a confirmação literal `RESTAURAR BACKUP`.
- **Recrutador:** não vê gestão de usuários nem restauração, e a API devolve HTTP 403 se tentar essas operações.
- **Senhas de contas individuais:** criação de conta, troca de senha no primeiro acesso e redefinição passam a aceitar 8 a 256 caracteres, com letras e números. A senha principal (`ENTREVISTADOR_ADMIN_PASSWORD`) continua exigindo pelo menos 16 caracteres.
- **Identificação da versão:** interface e `/api/health` mostram a V9.6.4.

## ANTES DE IMPLANTAR

**O Render Free não possui armazenamento persistente.** Faça o download do backup atual e abra o ZIP para verificar `dados.sqlite3` e as gravações na pasta `arquivos/` antes de qualquer deploy. Salve a cópia em local privado, como sua pasta Google Drive. Se o backup estiver incompleto, **não publique** a atualização até recuperar os arquivos. A restauração é uma operação que substitui o banco e os anexos da instância atual; ela não faz uma mesclagem.

## Atualização manual no GitHub

Substitua somente estes arquivos, exatamente nos caminhos indicados:

1. `server.py` na **raiz** do repositório.
2. `static/index.html` na pasta `static/`.
3. `static/app.js` na pasta `static/`.

Faça **Commit changes** na branch conectada ao Render. Não altere `ENTREVISTADOR_ADMIN_PASSWORD`, `ENTREVISTADOR_PUBLIC_URL`, o Dockerfile ou os demais arquivos.

## Publicação no Render

1. Abra o serviço `entrevistador-digital`.
2. Clique em **Manual Deploy > Deploy latest commit**.
3. Aguarde o serviço ficar **Live**.
4. Confira `https://entrevistador-digital.onrender.com/api/health`; o campo `version` deve ser `9.6.4-admin-backup-passwords`.
5. Abra o sistema em janela anônima para evitar cache. Entre como administrador.
6. Verifique o botão **Restaurar backup ZIP**, a aba **Backup e restauração** e a senha mínima de 8 caracteres na aba **Usuários e acessos**.

## Restauração

1. Antes de restaurar, baixe outro backup do estado atual se houver dados a preservar.
2. Abra **Backup e restauração**, selecione o arquivo ZIP e digite exatamente `RESTAURAR BACKUP`.
3. Confirme a substituição. O sistema irá validar a estrutura do arquivo; após restaurar, as sessões serão encerradas e será necessário efetuar login novamente.

## Validação executada

- 7 testes de integração e regressão passaram, incluindo permissões de administrador secundário e recuperação de arquivo de áudio fictício.
- Interface verificada com navegador Chromium local, usando respostas simuladas da API: botão e aba aparecem para administrador e ficam ocultos para recrutador; sem exceções de JavaScript.
- Código Python compilado e JavaScript validado com `node --check`.
- A atualização **não foi implantada na sua conta Render**; a verificação do serviço real ainda depende do seu deploy.

**Limite atual:** isso não corrige a transcrição com `faster_whisper`, nem o armazenamento temporário do Render Free.

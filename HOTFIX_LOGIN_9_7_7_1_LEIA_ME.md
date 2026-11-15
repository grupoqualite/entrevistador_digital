# Qualité Entrevistar Digital | Correção emergencial do login 9.7.7.1

## Falha comprovada no pacote 9.7.7 entregue
O arquivo `static/index.html` declarava `ed-ui-version=9.7.7-parecer-qualite`, mas `static/app.js` exigia `9.7.5-disc-brand`. O JavaScript interrompia a inicialização, inclusive a função de login. **Esse foi um erro de integração do pacote entregue, não de senha**.

## Correção
- `static/app.js`: agora valida `9.7.7-parecer-qualite`, compatível com a página e a API, e exibe a versão corretamente.
- `static/index.html`: muda o identificador de cache do script para `qualite-9771-login`, evitando reutilizar o JavaScript incompatível salvo no navegador.
- `tests/test_login_9771_regression.py`: impede que o erro passe novamente sem ser detectado nos testes.

## Como implantar (manual)
1. Não apague o serviço, o banco nem as variáveis de ambiente no Render. Não altere sua senha.
2. Faça upload para o GitHub de **ambos os arquivos** `static/app.js` e `static/index.html` do pacote de correção, mantendo seus diretórios.
3. Faça commit e no Render rode `Manual Deploy → Deploy latest commit`, no serviço existente.
4. Abra o painel em uma janela anônima ou atualize forçando o recarregamento (`Ctrl+Shift+R`).
5. Use **admin** no campo de usuário e a senha já configurada em `ENTREVISTADOR_ADMIN_PASSWORD` nas variáveis de ambiente do serviço Render. Não envie essa senha aqui.
6. O endpoint `/api/health` continua exibindo `9.7.7-parecer-qualite`, porque a correção é somente da interface de login.

## Se ainda não entrar
Se aparecer `Usuário ou senha incorretos`, confirme que você está entrando como `admin` e usando a senha efetiva no serviço **correto** do Render. Se aparecer `Muitas tentativas`, aguarde 15 minutos sem novas tentativas. Se a tela acusar versões diferentes, confira se **ambos** os arquivos foram publicados e recarregue sem cache. Não faça restauração ou substituição do banco para resolver login.

## Escopo
Esta correção não mexe no banco, no hashing de senhas, nos usuários, nos pareceres nem nos dados dos candidatos.

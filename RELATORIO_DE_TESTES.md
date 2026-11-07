# Validação local da versão 9.5

**Testes concluídos no ambiente local:**

- Compilação Python de `server.py` e `engine.py`.
- Verificação de sintaxe JavaScript de `static/app.js`.
- Cinco testes de regressão com pytest.
- Login do administrador principal, criação de conta individual, troca de senha provisória, perfis e acesso negado à gestão de usuários para recrutadores.
- Cadastro de vaga financeira, geração e regeneração de questionário, salvamento de edição e desativação de usuário.
- Exemplos de roteiro para vendas, finanças, obras, marketing e dados, com categorias e perguntas específicas por competência.

**Não validados:**

- Navegação completa com microfone real no Safari ou Chrome do celular.
- Execução real do Whisper Tiny ou motor de avaliação semântica no Render Free.
- Persistência dos dados após hibernação/reinício do Render Free (conhecidamente indisponível nesse plano com armazenamento local).
- Publicação no repositório GitHub do usuário e deploy na conta do usuário (não conectados para escrita nesta sessão).

O projeto é uma **atualização testável**, ainda não uma versão homologada para uso com candidatos reais.

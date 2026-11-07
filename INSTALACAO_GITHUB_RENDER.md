# Entrevistador Digital V9.5: implantação manual no GitHub e Render

## Antes de atualizar

Este é um **piloto**. O Render Free não fornece armazenamento persistente. Contas da equipe, vagas, convites, arquivos, respostas, áudios e relatórios salvos no SQLite local podem desaparecer após inatividade, reinício ou novo deploy. **Não utilizar dados de candidatos reais enquanto a persistência e a recuperação de dados não estiverem implementadas e testadas.**

### Melhorias entregues

1. **Usuários:** administrador principal com login `admin` e senha definida no Render; contas adicionais por e-mail, dois perfis (Administrador/Recrutador), senha individual, troca obrigatória de senha provisória, desativação e redefinição. As senhas são armazenadas usando PBKDF2 e sal individual. Recrutadores não gerenciam usuários.
2. **Gerador de perguntas:** lê os requisitos efetivamente extraídos da descrição; classifica responsabilidades, conhecimentos técnicos e comportamentos; apresenta pergunta contextual, evidência esperada e trecho da origem; separa diferenciais dos obrigatórios; não introduz habilidades ausentes como critério.
3. **Regeneração:** botão **Regenerar roteiro contextual** para vagas cadastradas **que ainda não tenham convites**. Regenerar substitui o roteiro atual; revise antes de convidar.
4. Permanecem o registro de entrevistas, upload de documentos, transcrição experimental e dossiê no padrão aprovado de três seções.

### Arquivos para substituir no GitHub

Use `PATCH_V9_5_4_ARQUIVOS.zip`. Dentro dele há quatro arquivos:

- `server.py` (raiz)
- `engine.py` (raiz)
- `static/app.js`
- `static/index.html`

Substitua **exatamente nesses caminhos**, sem criar uma pasta adicional ao redor. Não altere as variáveis do Render e **não** envie o ZIP compactado ao repositório. Confirme o commit na branch usada pelo serviço, geralmente `main`.

### Novo deploy no Render (sem Blueprint)

Render > serviço `entrevistador-digital` > **Manual Deploy** > **Deploy latest commit**. Aguarde a mensagem `Your service is live`.

Abra a URL existente em janela privada. Verifique `https://entrevistador-digital.onrender.com/api/health`: `version` deverá ser `9.5-users-questions`.

### Entrar e criar usuários

Administrador principal: `admin` + valor secreto de `ENTREVISTADOR_ADMIN_PASSWORD` definido em Render > Environment. Não use a senha da conta Render.

Na aba **Usuários e acessos**, cadastre nome, e-mail, perfil e senha provisória (mínimo de 16 caracteres, contendo letras e números). Compartilhe as credenciais por canal privado. No primeiro login, o usuário será obrigado a trocar a senha.

As contas persistem somente enquanto o sistema de arquivos efêmero da instância existir. **A criação de usuários não resolve a perda de dados do Free.**

### Testar o roteiro

1. Crie uma vaga fictícia e importe a descrição (PDF, DOCX, XLSX, XLS, TXT ou CSV), ou cole a descrição.
2. Confira a extração e a divisão em abas/páginas antes de clicar em **Gerar questionário fundamentado**.
3. Em **Revisar perguntas**, confira categoria, foco, evidência esperada e trecho literal da vaga.
4. Edite e salve antes de criar convite. Para vagas antigas sem convites, clique em **Regenerar roteiro contextual**.
5. Faça uma entrevista com dados fictícios e confira respostas e revisão de parecer.

### Diagnóstico

- `403` na aba Usuários: a conta logada é Recrutador, não Administrador.
- `409` ao regenerar perguntas: vaga já possui convites; crie nova vaga para não modificar perguntas de entrevistas existentes.
- `401` de login: confira usuário `admin` para a conta principal ou e-mail para contas adicionais.
- Se os controles não mudarem após o deploy, abra janela anônima e verifique versão no endpoint `/api/health`.

### Limitações explícitas

O motor gratuito é **baseado em regras e bibliotecas de perguntas por atividade**, não um modelo de linguagem que compreenda perfeitamente qualquer documento. Vagas muito específicas exigirão revisão e edição humana. Sem Ollama, o sistema não realiza análise semântica automática de todas as respostas nem produz nota técnica confiável de forma autônoma. A transcrição com Whisper Tiny no Render Free ainda precisa de homologação real e pode falhar por recursos insuficientes.

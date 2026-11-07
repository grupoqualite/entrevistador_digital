# Correção V9.3 | Importação de vagas e geração do questionário

## O que foi corrigido

- Corrigida a função que preenche os seletores (`option(elementId, value, label)`). O erro anterior atribuia o nome do campo como valor da opção, quebrando a seleção das abas de Excel, das vagas criadas e dos candidatos.
- Em documentos com uma única seção, o texto extraído já é inserido no campo de descrição, pronto para conferência.
- Em documentos com várias páginas/abas, mantenha a seleção e clique em **Aplicar texto selecionado** antes de gerar o roteiro.
- Melhoradas as mensagens de importação e a versão do script para evitar cache desatualizado no navegador.
- A ação de aprimoramento por modelo de linguagem foi sinalizada como indisponível no piloto Render Free, pois depende de um modelo local que não está configurado. **Gerar questionário fundamentado** funciona sem esse modelo.

## Como aplicar no GitHub

1. Entre no repositório usado pelo Render, na branch `main`.
2. Abra a pasta `static`.
3. Substitua **somente** os arquivos `app.js` e `index.html` pelos dois arquivos desta correção, sem criar uma segunda pasta `static` dentro da primeira.
4. Confirme o commit.
5. Em Render > Manual Deploy > Deploy latest commit.
6. Faça uma recarga forçada do site após o deploy (Ctrl+Shift+R no computador, ou nova guia privada no celular).
7. Abra Vagas e roteiro > Importar descrição da vaga; confira o texto e clique em Gerar questionário fundamentado. O painel Revisar perguntas deve mostrar o roteiro.

## Testes realizados neste pacote

- Teste de interface em navegador com largura de celular, usando respostas de API simuladas: login de teste, importação TXT, seleção correta, criação de vaga e carregamento do roteiro.
- Testes reais das rotas FastAPI de importação TXT, DOCX e XLSX (duas abas) e criação de vaga financeira fictícia: cinco perguntas, cobrindo responsabilidades, hard skills e soft skills.
- Sintaxe do JavaScript verificada com Node.

## Limitações

- Esta correção não muda o backend `server.py`, as senhas nem a transcrição.
- O teste não equivale à validação da publicação no Render: após o commit, confira o comportamento no seu endereço `onrender.com`.
- O Render Free mantém armazenamento efêmero; um redeploy pode apagar vagas, entrevistas e arquivos locais. Faça cópia prévia de quaisquer dados de teste importantes. **Não utilize candidatos reais** antes de configurar armazenamento persistente e validar segurança e transcrição.

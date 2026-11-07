# Entrevistador Digital V9.6.2 – Correção do anexo de documentos

## Erro identificado
Na V9.6.1, em `static/app.js`, o envio dos materiais fazia `await call(...)` e, em seguida, chamava `e.currentTarget.reset()`. Nos eventos de formulário do navegador, `event.currentTarget` pode ser nulo depois da conclusão do despacho do evento, mesmo que a requisição tenha sido processada e gravada pelo servidor. Isso provoca a mensagem "Cannot read properties of null (reading 'reset')" e substitui uma confirmação de upload por erro.

## Corrigido nesta atualização
- O formulário e o candidato são capturados antes da primeira operação assíncrona.
- O botão é desabilitado durante o envio, prevenindo cliques duplicados.
- Os campos de arquivo são limpos apenas após confirmação HTTP de sucesso.
- A interface atualiza a situação das fontes e mostra quantos caracteres foram extraídos.
- Se a atualização visual falhar após o upload, o sucesso do envio continua visível.
- Erros do servidor mantêm os arquivos selecionados e orientam conferir o cadastro antes de reenviar.
- Versões de HTML, JavaScript e `/api/health` sincronizadas como `9.6.2-upload-fix`, com cache busting.
- O backup gerado pelo servidor usa snapshot SQLite consistente, inclusive com modo WAL, para novos backups criados após o deploy desta versão.

## Cuidado antes da atualização: Render Free não tem disco persistente
**Antes de implantar um novo commit, o serviço atual pode perder banco e documentos ao reiniciar.**
1. No painel ainda aberto, selecione o candidato na seção Entrevistas e dossiês e confira se aparecem `Currículo ✓`, `DISC ✓` e `LinkedIn exportado ✓` no resumo. O erro de JavaScript pode ter acontecido após um envio que foi efetivamente salvo.
2. Baixe **Baixar backup para guardar no Drive** e conserve esse ZIP em pasta privada de acesso restrito. O backup atual (V9.6.1) não usa snapshot SQLite; dados muito recentes no WAL podem não estar incluídos. Portanto, não o considere garantia absoluta e mantenha também os arquivos originais em local seguro.
3. Não envie documentos reais ao Render Free enquanto não houver armazenamento persistente e controle de privacidade adequados.

## Instalação no GitHub
Substitua os seguintes arquivos em **um único commit**, preservando a estrutura:
- `server.py` (raiz)
- `static/index.html`
- `static/app.js`

Os demais arquivos devem permanecer intocados: `engine.py`, `evidence_draft.py`, demais arquivos na pasta `static`, dados e configurações.

No Render: **Manual Deploy > Deploy latest commit**. Ao ficar Live, confira `https://entrevistador-digital.onrender.com/api/health` e o campo `version` = `9.6.2-upload-fix`. Reabra o painel em guia anônima. A interface mostrará `V9.6.2`.

## Testes executados em ambiente de desenvolvimento
- Fluxo de formulário em Chromium: 1) envio de CV e DISC com retorno assíncrono, sucesso, refresh e reset; 2) erro 422 e retenção dos arquivos, sem exceção JavaScript.
- API FastAPI: importação de currículo, DISC e perfil LinkedIn fictícios, confirmação de extração e leitura dos documentos, geração de backup e versão do health.
- Cinco testes de regressão preexistentes, sintaxe do JavaScript e compilação do Python.

**Não foi realizado deploy nesta conta Render**, nem teste de envio de documentos reais. Publicação e reinicialização dependem do proprietário da conta.

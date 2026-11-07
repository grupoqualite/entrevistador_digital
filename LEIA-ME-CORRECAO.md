# Correção V9.6.1 | Identificação e sincronização da versão

## Diagnóstico
A V9.6 original possui o motor atualizado e responde `9.6-evidence-draft` no endpoint `/api/health`, mas os arquivos de interface foram publicados com o identificador visual `9.5.1-login-sync`. Portanto o cabeçalho e a referência do script podiam continuar em V9.5.1 mesmo quando o servidor já estava atualizado.

## Instalação no repositório privado do GitHub
1. Abra **a mesma branch e o mesmo repositório conectados ao serviço no Render**.
2. Na **raiz**, substitua `server.py`, `engine.py` e adicione/substitua `evidence_draft.py`.
3. Dentro da pasta **static** existente, substitua `index.html` e `app.js`. Não crie uma segunda pasta `static`.
4. Confirme os cinco arquivos em **um único commit**. Não altere as senhas nem as variáveis de ambiente.
5. No Render, em **Manual Deploy**, escolha **Deploy latest commit**. Confira se o hash do commit publicado corresponde ao do GitHub.
6. Quando estiver live, acesse `https://entrevistador-digital.onrender.com/api/health`. O campo `version` deve ser `9.6.1-evidence-draft`.
7. Abra o painel em guia anônima. O cabeçalho deverá mostrar **V9.6.1**.

## Se os números forem diferentes
- `health = 9.5.1`: o Render ainda está com `server.py` antigo, ou a alteração foi enviada ao repositório/branch errados. Compare o commit no Render e no GitHub.
- `health = 9.6.1` mas painel = 9.5.1: o arquivo `static/index.html` antigo está no deploy ou o navegador está servindo cache. Revise o caminho e teste nova guia anônima.
- Ambos = 9.6.1: interface e backend estão sincronizados.

## Limites
Este ajuste de versão não ativa análise contextual automática. A minuta documental permanece não interpretativa sem motor de linguagem. No Render Free, dados locais, contas e entrevistas podem se perder a cada restart; não use dados reais sem armazenamento persistente, segurança e consentimento adequados.

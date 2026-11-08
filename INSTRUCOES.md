# Correção de identificação de versão V9.6.3 (painel e servidor)

## Motivo
No pacote V9.6.3, `server.py` retornava `9.6.3-backup-restore` em `/api/health`, mas `static/index.html` ainda mostrava `V9.6.2` em texto fixo. Isso não prova que o servidor não tenha sido atualizado.

## O que foi alterado
- `static/index.html`: mostra **Verificando versão...** até o diagnóstico retornar.
- `static/app.js`: consulta `/api/health` sem cache e mostra a versão realmente executada pelo Render. Se estiver diferente, informa a divergência no painel.
- A URL do JS usa um novo marcador de cache, evitando que o navegador reaproveite o script antigo.

## Instalação
1. **Antes do deploy**, baixe o backup do sistema e confira o conteúdo. A instância Render Free não oferece persistência de dados.
2. No GitHub, **substitua apenas** `static/index.html` e `static/app.js`, mantendo os diretórios.
3. Confirme os arquivos no `main` e faça Commit changes.
4. No Render, use **Manual Deploy > Deploy latest commit** e acompanhe a conclusão.
5. Abra `https://entrevistador-digital.onrender.com/api/health` e confirme o campo `version`.
6. Abra o painel em janela anônima. Ele passa a mostrar a versão obtida do servidor.

## Diagnóstico
- Se `/api/health` mostrar `9.6.3-backup-restore`, o backend V9.6.3 está ativo. Se o painel era V9.6.2, tratava-se apenas do texto fixo ou do cache.
- Se `/api/health` ainda mostrar `9.6.2` ou outro valor antigo, o Render está executando um backend anterior: confira branch, Root Directory, último commit implantado e `server.py` na raiz.
- Se a tela mostrar **Versão não verificada**, há uma falha ao consultar o diagnóstico; confira Network e logs.

## Escopo
Esta atualização corrige **apenas a identificação da versão**. Não modifica senhas, usuários, restauração de backup, entrevistas ou transcrição. **Não corrige o erro de dependência `faster_whisper`.**

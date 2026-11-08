# Entrevistador Digital V9.6.3 | Backup e restauração

## O que foi alterado

- Todos os **usuários ativos com perfil Administrador** podem baixar e restaurar backups. Não é necessário entrar com a conta principal.
- Usuários com perfil **Recrutador** não podem baixar nem restaurar backups completos. Um usuário com senha provisória pendente de troca precisa alterá-la antes de acessar essa função.
- A área **Usuários e acessos → Restaurar backup** permite enviar um ZIP criado pelo Entrevistador Digital.
- Antes de substituir dados, o sistema valida a estrutura ZIP, o banco SQLite e os anexos referenciados, e solicita a frase de confirmação `RESTAURAR BACKUP`.
- O sistema registra no histórico interno a identidade do administrador responsável pela restauração e o identificador criptográfico do arquivo.
- A restauração recupera vagas, candidatos, usuários, respostas, áudios, materiais anexados, pareceres e logotipo (quando presente no backup).
- Todas as sessões são encerradas. É necessário fazer login novamente com uma conta existente no backup ou com a credencial administrativa principal configurada no Render.
- O download foi alterado para transmissão por arquivo temporário, evitando manter o ZIP inteiro na memória RAM.

## Antes de instalar no Render

**Faça o download de um backup da instalação atual antes de publicar outro commit.** O plano gratuito do Render tem armazenamento efêmero. Um deploy pode perder o banco e os áudios atuais. Verifique que o ZIP foi salvo no Google Drive privado e que contém `dados.sqlite3` e os áudios na pasta `arquivos/`.

1. Extraia `Entrevistador_Digital_V9_6_3_Backup_Restore_GitHub.zip`.
2. Atualize **somente** os arquivos `server.py` (raiz), `static/index.html` e `static/app.js` no GitHub. Mantenha os caminhos originais.
3. Faça commit na branch que o Render acompanha e use **Manual Deploy → Deploy latest commit**.
4. Confirme `https://entrevistador-digital.onrender.com/api/health`. O campo `version` deverá ser `9.6.3-backup-restore`.
5. Entre como Administrador, acesse **Usuários e acessos → Restaurar backup**, escolha o arquivo ZIP, digite `RESTAURAR BACKUP` e confirme.
6. Aguarde a confirmação. Faça novo login e verifique a quantidade de vagas, candidatos, respostas, áudios e contas recuperadas.

## Permissões

| Perfil | Baixar backup completo | Restaurar backup |
|---|---|---|
| Administrador principal | Sim | Sim |
| Administrador secundário ativo | Sim | Sim |
| Recrutador | Não | Não |

A restauração substitui os registros atuais pelos do backup, inclusive a relação de usuários e senhas individuais. A senha principal definida pela variável `ENTREVISTADOR_ADMIN_PASSWORD` **não** é armazenada no backup e permanece administrada pelo Render.

## Proteções incluídas

- Upload limitado a 210 MB comprimidos e a 220 MB descompactados; no piloto, backups maiores exigirão outro procedimento.
- Rejeição de caminhos externos (`../`), links simbólicos, duplicação de entradas, arquivos inesperados e bancos SQLite inválidos.
- Conferência de integridade do banco, tabelas e existência dos anexos referenciados.
- Bloqueio se houver análise ou transcrição em andamento.
- Cópia temporária para retorno ao estado anterior se a substituição falhar durante a troca dos arquivos.
- Auditoria de quem realizou a restauração e encerramento de todas as sessões.

## O que esta atualização não resolve

A hospedagem no Render Free continua **sem armazenamento persistente**. Um backup recuperado poderá ser perdido em novo deploy/hibernação, por isso deve permanecer guardado fora do servidor. A função não sincroniza automaticamente com o Google Drive nem corrige a biblioteca ausente `faster_whisper` para transcrição. Ela também não valida dados reais no ambiente Render; os testes de restauração foram locais e com dados fictícios.

O ZIP contém dados pessoais, arquivos profissionais, DISC e áudios e não é criptografado por padrão. Guarde em pasta privada do Drive com acesso restrito. Não compartilhe o backup em links públicos.

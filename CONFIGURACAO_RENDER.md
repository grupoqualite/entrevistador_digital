# Instalar no Render SEM Blueprint, sem contratar instância paga

> **Este pacote é apenas para TESTE com dados fictícios.** Render Free possui 512 MB RAM, CPU limitada e armazenamento efêmero. Sem disco persistente, **todos os uploads, banco de dados e áudios são perdidos** a cada hibernação (15 min sem acesso), reinicialização ou novo deploy. O serviço não é adequado para recrutamento real. Não há integração automática com Google Drive.

## 1. GitHub

Crie um repositório **privado** `entrevistador-digital`.

Descompacte o ZIP e envie o conteúdo para a **raiz**: `Dockerfile`, `server.py`, `render_entrypoint.py`, `requirements-render.txt`, pasta `static/` etc.

Não envie o próprio arquivo ZIP, nem arquivos `.env`, senhas, `dados/` ou documentos de candidatos.

**Não há `render.yaml` neste pacote.** Isso evita a criação automática de serviços pagos por Blueprint.

## 2. Criar Web Service manualmente

Entre em https://dashboard.render.com/ e abra **New > Web Service** (não Blueprint).

| Campo | Valor a selecionar |
|---|---|
| Source | Git provider: GitHub, repositório privado criado |
| Name | `entrevistador-digital-piloto` ou outro nome livre |
| Language/Runtime | **Docker** |
| Branch | `main` |
| Dockerfile Path | `./Dockerfile` |
| Docker Build Context | `.` ou raiz do repositório |
| Instance Type / Compute Plan | **Free, US$ 0/mês** |
| Region | escolha próxima dos candidatos, se disponível |
| Health Check Path | `/api/health` |
| Disk | **Nenhum. Não adicione disco.** |
| Auto-Deploy | `Off` durante o piloto para evitar builds desnecessários |

Não configure Build Command nem Start Command para runtime Docker. O `CMD` do Dockerfile usa a porta `$PORT` do Render via `render_entrypoint.py`.

## 3. Environment variables (Environment > Add Environment Variable)

Defina **valores próprios e verdadeiros**, sem credenciais no GitHub:

| Key | Value |
|---|---|
| `ENTREVISTADOR_ENV` | `production` |
| `ENTREVISTADOR_DATA` | `/tmp/entrevistador-digital` |
| `ENTREVISTADOR_ADMIN_PASSWORD` | **Senha forte exclusiva de 16+ caracteres** |
| `ENTREVISTADOR_CONTROLLER_NAME` | **Nome da empresa responsável pelo teste** |
| `ENTREVISTADOR_PRIVACY_CONTACT` | **E-mail de contato válido** |
| `ENTREVISTADOR_RETENTION_DAYS` | `1` (somente informação de prazo, não faz exclusão automática) |
| `ENTREVISTADOR_WHISPER_MODEL` | `/opt/whisper/tiny` |
| `ENTREVISTADOR_OLLAMA_MODEL` | deixe vazio |

**Não configure `ENTREVISTADOR_PUBLIC_URL`**. `render_entrypoint.py` usa `RENDER_EXTERNAL_URL` automaticamente quando o Render iniciar. Se o log reclamar de URL, coloque a URL HTTPS **real** exibida pelo Render, sem barra final. Nunca invente uma URL.

## 4. Confirmar antes de criar

Na tela final, confirme que está **Free** e sem persistent disk, banco pago ou worker pago. Se houver cobrança ou não existir o plano Free, **não confirme**.

Em Billing e Workspace Settings > Build Pipeline configure limite de gastos de minutos extras igual a **US$ 0, se a interface aceitar**, e confira os limites de banda. O limite de minutos de build não é um teto universal para outras cobranças; acompanhe o painel de billing.

## 5. Teste pelo celular

Abra o endereço HTTPS que o Render gerar. O serviço gratuito pode levar cerca de 1 minuto para iniciar após ficar inativo.

1. Acesse `/api/health`, confira `ok:true`, `pilot_only:true` e o aviso de armazenamento efêmero.
2. Entre no painel com a senha cadastrada.
3. Crie uma vaga **fictícia** com responsabilidades, hard skills e soft skills, gere e revise o questionário.
4. Cadastre um **candidato fictício**, gere o convite, abra-o no celular pelo link HTTPS.
5. Responda ao menos uma pergunta em áudio e conclua a entrevista.
6. Volte ao painel, na área de entrevistas, e confira a fila de transcrição e o texto reconhecido.
7. Se a instância for reiniciada, tudo poderá ser perdido. Faça o teste numa única sessão ativa.

O pacote usa **Whisper tiny multilíngue**. Ele pode gerar transcrição com erros ou falhar por consumo de memória/tempo no Free. Não há garantia de desempenho nem pontuação técnica automática por modelo de linguagem neste plano. A função de parecer técnico continua sujeita à revisão humana.

## 6. O que analisar nos logs

- `Out of memory` / `Killed`: o modelo Tiny está excedendo a RAM; não aumente automaticamente o plano.
- `Build failed`: consulte as últimas linhas de Logs / Events, envie a mensagem de erro.
- `Port scan timeout`: confira `render_entrypoint.py` e `PORT` (o código atual usa `$PORT`).
- `/api/health` responde 200 mas login não funciona: revise env vars e senha.
- `Transcription failed`: verifique o áudio e o estado da fila.

## 7. Dados persistentes e Google Drive

A pasta `Entrevistador Digital - Testes` foi criada no Google Drive, mas **o Render não a acessa por meio do plugin do ChatGPT**. Será necessário implementar uma autenticação OAuth da aplicação e sincronização controlada para armazenar arquivos e metadados de modo durável. Não considere o botão de exportar backup uma sincronização automática.

O serviço Free e seu banco temporário **não podem ser usados com dados reais**. Para passar a entrevistas reais sem contratar um disco pago, precisamos primeiro implementar armazenamento durável remoto com controle de acesso, consentimento/informações adequadas e testes de recuperação.

Documentação Render: https://render.com/docs/free e https://render.com/docs/web-services

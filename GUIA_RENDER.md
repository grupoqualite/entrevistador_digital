# Guia de implantação | Render com transcrição automática

Este pacote é para **um repositório privado novo no GitHub**. Não precisa mexer nos demais serviços do Render.

## Limites e custos antes de confirmar

- O Blueprint usa o plano de EXECUÇÃO **`1c-2g` (1 CPU, 2 GB RAM)**, que não é o plano Starter do build pipeline mostrado em sua captura. Em novembro/2026, o preço de referência publicado é US$ 25/mês, mais disco SSD (2 GB), impostos e eventuais extras.
- Não use o plano web `starter` (512 MB): ele pode falhar com o Whisper e as dependências do sistema.
- O modelo **faster-whisper base multilíngue** é baixado no Docker BUILD e executado no Render usando CPU. Não compra tokens.
- A transcrição pode demorar, principalmente em áudios longos. O sistema enfileira o trabalho após a conclusão da entrevista, registra o progresso e oferece reprocessamento.
- **Não há Ollama na instância web**. Portanto, a aderência técnica automática e a redação contextual por um modelo local continuam sem funcionamento no Render 2 GB até configurar um motor de análise separado. A plataforma permite avaliação fundamentada pelo recrutador e não atribui notas falsas.

## Implantação

1. Crie no GitHub um repositório privado `entrevistador-digital` (ou outro nome).
2. Extraia o ZIP e envie para a **raiz** do repositório os arquivos e pastas, incluindo `render.yaml`, `Dockerfile.render`, `static/` e `server.py`. Não envie o ZIP inteiro como arquivo único.
3. Não envie `.env`, `dados/`, `.sqlite3`, áudios de candidatos ou senhas. O `.dockerignore` protege parte desses arquivos, mas confira também o `.gitignore`.
4. No Render, clique em **New > Blueprint**, conecte o repositório e revise o serviço proposto `entrevistador-digital-teste`.
5. **Antes de criar**, revise plano `1c-2g`, disco de 2 GB e o custo indicado na sua conta. Se exceder seu orçamento, não aplique o Blueprint.
6. Informe diretamente no Render os valores secretos `ENTREVISTADOR_ADMIN_PASSWORD` (senha exclusiva de 16+ caracteres), `ENTREVISTADOR_CONTROLLER_NAME` (empresa responsável) e `ENTREVISTADOR_PRIVACY_CONTACT` (e-mail de contato). Não coloque credenciais no GitHub.
7. Aguarde o deploy concluído e verifique o endereço real gerado pelo Render. O `render_entrypoint.py` obtém o HTTPS de `RENDER_EXTERNAL_URL` e usa a porta `$PORT`.
8. Abra `https://ENDERECO-REAL/api/health` e confirme `ok: true`. Entre com a senha no painel.
9. Com **vaga e candidato fictícios**, importe a descrição, gere perguntas por responsabilidades/hard/soft skills, cadastre um candidato e abra o link individual em celular com HTTPS.
10. Responda uma pergunta em áudio e conclua a entrevista. No painel de **Análise das entrevistas**, acompanhe `Na fila → Transcrevendo → Transcrição concluída`. Confira o texto e corrija manualmente se necessário, sempre comparando com o áudio original.
11. Clique em **Organizar evidências da entrevista** e revise o material. O PDF para cliente exige ratificação/retificação e as três seções aprovadas. A avaliação automática por modelo de linguagem **não** está ativada no plano de 2 GB.

## Funcionamento e segurança

- Os áudios, documentos, banco SQLite e relatórios são salvos em `/app/dados`, disco persistente privado de um serviço do Render. Sem o disco, serão perdidos em reinicializações.
- O download de backup pelo painel é manual; a pasta do Google Drive criada anteriormente **não está sincronizada** com o Render.
- Reinicialização enquanto transcreve marca o trabalho como interrompido; o recrutador usa **Reprocessar áudios pendentes**. Transcrições já salvas são preservadas.
- Áudio sem voz reconhecível ou erro na transcrição deixa pendência visível e bloqueia o processamento da análise, em vez de inventar respostas.
- O modelo foi pré-instalado, portanto não depende de baixar do Hugging Face a cada entrevista.
- Um único serviço, um worker sequencial e um banco SQLite: **piloto controlado**, não infraestrutura dimensionada para muitas entrevistas simultâneas.
- Antes de usar candidatos reais, valide permissões de acesso, política de retenção, proteção das informações e segurança do serviço. O teste integrado foi executado com dados fictícios.

## Critério de aceitação da transcrição

- [ ] Áudio gravado no Safari e Chrome por HTTPS.
- [ ] Conclusão da entrevista cria trabalho de transcrição automaticamente.
- [ ] O painel mostra andamento até finalizar.
- [ ] O áudio e seu texto continuam disponíveis após uma atualização de página.
- [ ] A análise não trata um áudio não transcrito como evidência.
- [ ] Falhas podem ser reprocessadas sem perder os demais áudios.

### Identidade visual no piloto
Na tela inicial do painel há um campo opcional para enviar o logotipo (PNG ou JPG). Sem envio, o cabeçalho do PDF continua neutro, sem marca inventada. SVG dependerá de sanitização e conversão segura em outra etapa.

### Permissões do disco
O `docker_entrypoint_render.sh` prepara a propriedade da raiz do disco ao iniciar, depois reduz os privilégios do processo usando `gosu`. Isso evita falhas de escrita quando o Render monta um volume inicialmente pertencente ao usuário root.

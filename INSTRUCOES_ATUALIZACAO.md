# Entrevistador Digital V9.7.0 | Parecer gerável no Render Free

## O que esta atualização faz

- Ao concluir uma entrevista **por texto**, o servidor prepara automaticamente a minuta do parecer usando as respostas e os documentos que realmente conseguir ler.
- Para entrevistas **já concluídas**, selecionar o candidato na aba **Entrevistas e dossiês** preenche automaticamente uma minuta ausente ou incompleta. O botão **Gerar ou atualizar minuta do dossiê** permite repetir a preparação quando ainda não há revisão humana salva.
- A minuta vem com três seções: **Competências Técnicas**, **Competências Comportamentais** e **Parecer de Recomendação**. O texto não apresenta cálculos, pesos ou nome de tecnologia.
- **Baixar prévia PDF (minuta)** funciona sem exigir a pontuação de todos os critérios, mas o PDF vem marcado como minuta e não deve ser enviado ao cliente.
- Para liberar o **PDF final**, revise as fontes e as três seções, clique **Salvar texto revisado** e depois **Aprovar parecer para o cliente**. A aprovação é registrada por usuário. Editar o texto revoga essa aprovação até nova conferência.
- Áudios antigos sem transcrição não são descartados ou inventados: constam como pendências. Novas entrevistas continuam exclusivamente por texto.
- Regras de usuários, restauração de backups, senhas de 8 caracteres para usuários individuais e login foram preservadas.

## Limite técnico importante

A redação automática gratuita é **documental e baseada em evidências literais**. Ela **não executa avaliação semântica profunda**, não atribui nota técnica automaticamente e **não transforma o DISC em nota**. Para atingir a qualidade analítica de um dossiê elaborado por um especialista, o recrutador deve interpretar as fontes e editar/ratificar as três seções. O Ollama permanece opcional e não foi instalado pelo pacote.

## Atualizar no GitHub e Render

1. Confirme que o **backup atual** está guardado em local privado e contém o banco e os anexos. Você informou que já o realizou; confirme a integridade antes de atualizar.
2. Extraia o arquivo de atualização e substitua no repositório privado **exatamente** os arquivos mantendo os caminhos:
   - `server.py` (raiz)
   - `evidence_draft.py` (raiz)
   - `client_report.py` (raiz)
   - `static/index.html`
   - `static/app.js`
   - `static/interview.html`
3. Faça commit na branch `main`.
4. No Render, faça **Manual Deploy → Deploy latest commit**. Não use Blueprint e não mude o plano.
5. Confira `https://entrevistador-digital.onrender.com/api/health` e confirme a versão `9.7.0-documental-review`.
6. Se o banco tiver sido apagado pelo redeploy, entre como administrador e restaure seu backup na área **Backup e restauração**, depois entre novamente. Restauração substitui todos os registros, inclusive usuários.
7. Abra **Entrevistas e dossiês**, selecione um candidato já concluído e confira os campos **Competências Técnicas**, **Competências Comportamentais** e **Parecer de Recomendação**. Use **Baixar prévia PDF** para inspecionar o formato.
8. Ajuste fatos, lacunas e conclusão, clique **Salvar texto revisado**, depois **Aprovar parecer para o cliente**. Só então estará disponível **Baixar parecer aprovado PDF**.

## Antes de usar com candidatos reais

**Não coloque dados pessoais reais no Render Free enquanto o banco e os anexos estiverem apenas no armazenamento temporário.** Hibernação, reinicialização e novo deploy podem eliminar arquivos e registros; backup manual não equivale a persistência automática. É indispensável implantar armazenamento durável, política de retenção, segurança dos documentos e procedimento de recuperação, além de validar as permissões e a privacidade dos dados.

## Rollback

Se ocorrer algum erro, restaure o commit anterior pelo GitHub/Render e o backup privado correspondente. O pacote **não** inclui banco, currículos, áudios ou senhas.

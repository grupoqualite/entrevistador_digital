# V9.6 | Evidências, minutas e complemento de documentos

## Problema resolvido
A versão anterior exigia Ollama para gerar qualquer texto, mesmo quando havia entrevistas e currículos. No plano Render Free o Ollama não está instalado; por isso o botão falhava. Agora existe uma minuta documental **não interpretativa**, formada apenas por trechos efetivamente extraídos e respostas digitadas ou transcritas. Quando não houver fontes, ela apresenta erro descritivo e não inventa conteúdo.

## Fluxo correto
1. Crie vaga e revise os grupos de perguntas.
2. Cadastre candidato e anexe currículo, DISC, comparativo e perfil do LinkedIn exportado (URL não equivale a leitura do perfil).
3. Gere o link individual e conclua a entrevista.
4. Aguarde e confira a transcrição, se houver áudio.
5. Clique em **Organizar evidências da entrevista**.
6. A minuta técnica e comportamental aparecerá automaticamente, se existir conteúdo; você também pode clicar **Preencher minuta documental a partir das fontes**.
7. Ratificar/retificar cada critério, incluindo **sem nota** quando não houver evidência. Use a revisão humana para atribuir pontuações justificadas.
8. Revise e edite o texto das três seções, especialmente o Parecer de Recomendação, salve e baixe o PDF do cliente.

## Limite técnico obrigatório
- A minuta sem Ollama **não é interpretação semântica nem avaliação automática**: organiza as citações e explicita as lacunas, sem score sugerido.
- O dossiê híbrido final depende de revisão humana. Não afirmar experiência, resultado ou DISC sem fonte.
- Para notas automáticas contextualizadas e redação analítica equivalente aos modelos aprovados, é necessário implantar um motor de linguagem com capacidade compatível. O Render Free não hospeda Ollama 7B com 512 MB.
- A integração de áudio Whisper Tiny permanece experimental no Render Free e deve ser validada com áudio real.
- O armazenamento SQLite no Render Free continua **efêmero**: NÃO usar com dados reais antes de persistência externa e controles de segurança.

## Instalação
Substitua no GitHub: `server.py`, `evidence_draft.py` (novo), `engine.py`, `static/index.html`, `static/app.js`. Demais arquivos da V9.5.1 continuam como estão. No Render, faça deploy latest commit. `/api/health` => `9.6-evidence-draft`.

## Perguntas de perfil comportamental
O parser evita transformar frases sobre treinamento ou trechos de atividade operacional em soft skills. Perguntas já vinculadas a uma entrevista permanecem preservadas; gere uma nova vaga para utilizar o roteiro corrigido.

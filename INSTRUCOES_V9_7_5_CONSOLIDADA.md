# Entrevistador Digital V9.7.5: pacote único consolidado

Esta é uma **atualização da V9.7.5**, sem alteração do número principal da versão.
Inclui, em um único pacote, o leitor DISC Recrutei individual visual, a leitura do comparativo textual e o cabeçalho do parecer com logotipo opcional.

## O que muda

1. **DISC individual da Recrutei, três páginas, totalmente visual:** o sistema lê os quatro valores D/I/S/C de 1 a 7 pela posição dos marcadores no gráfico da página 3. Não depende de OCR nem de serviços externos. Se a diagramação do gráfico for diferente ou a detecção inconclusiva, apresenta pendência em vez de inventar escores.
2. **Comparativo DISC:** o relatório textual continua aceito, com a descrição do perfil e dimensões. O sistema preserva os dois documentos quando ambos forem fornecidos e sinaliza valores divergentes para conferência humana.
3. **Dossiê:** logotipo PNG/JPG configurado em "Entrevistas e dossiês > Identidade visual do parecer". A imagem aparece no cabeçalho do PDF. O PDF nunca exibe o nome "Entrevistador Digital" no cabeçalho e, sem logotipo, o cabeçalho é neutro. A identidade da empresa não aparece no formulário do candidato.
4. **Candidato existente:** opção "Reler DISC individual já anexado" permite reprocessar o arquivo visual conservado no servidor. O sistema exige nova avaliação de minuta e não permite substituir silenciosamente uma avaliação humana já aprovada.

## Limitações que permanecem

- O leitor gráfico foi validado **com o layout de três páginas fornecido**. Ele não reconhece automaticamente todos os PDFs DISC existentes e não extrai todos os parágrafos da imagem. Para extrair a descrição integral, use o comparativo textual, quando disponível, ou revisão humana do laudo.
- O DISC é apenas uma fonte complementar e não determina, por si só, competências demonstradas ou recomendação de contratação.
- A avaliação contextual automatizada por modelo de linguagem permanece indisponível no Render Free sem integração adicional.
- **Render Free não oferece armazenamento persistente.** Arquivos, logotipo, senhas de usuários, entrevistas e dados SQLite podem desaparecer após reinicialização/implantação. Faça backup antes de publicar e não dependa dessa instalação para guardar dados reais.

## Instalação manual sem Blueprint

1. Faça backup do sistema e guarde os PDFs originais antes de implantar.
2. Extraia o ZIP e envie os arquivos, preservando as pastas, para seu repositório GitHub privado.
3. Substitua os arquivos da raiz `server.py`, `engine.py`, `client_report.py`, `recrutei_disc.py`, `behavioral_analysis.py`, `integrated_review.py`, `evidence_draft.py` e os arquivos da pasta `static/` incluídos no pacote.
4. Faça commit na branch vinculada ao serviço do Render.
5. No Render, execute **Manual Deploy > Deploy latest commit**, sem alterar as senhas ou criar Blueprint.
6. Consulte `https://entrevistador-digital.onrender.com/api/health` e confira:
   - `version`: `9.7.5-disc-brand`
   - `build`: `disc-individual-visual-logo-consolidado`
7. Na seção "Entrevistas e dossiês", selecione um candidato; caso o DISC visual já esteja salvo, clique em **Reler DISC individual já anexado**. Se o arquivo tiver sido perdido no Render, reenvie-o pelo campo DISC.
8. Gere novamente a minuta, confira a interpretação do DISC, revise as três seções e só então aprove o parecer.
9. Na mesma seção, envie ou substitua o logotipo em "Identidade visual do parecer". Faça uma prévia e confira o cabeçalho.

## Validações locais realizadas

- PDF individual visual de três páginas fornecido: D5, I1, S7 e C4 identificados pelo gráfico.
- Comparativo do mesmo candidato: D5, I1, S7 e C4; perfil Realizador.
- Divergência simulada entre os PDFs: aviso exibido para conferência.
- PDF visual com gráfico desconhecido: rejeitado para pontuação automática.
- Fluxo de login, criação de vaga, cadastro de candidato, upload do DISC individual, anexo posterior do comparativo, releitura do arquivo salvo e inclusão posterior do currículo sem perder os dados anteriores: aprovado com dados de teste.
- PDF do cliente com logo: imagem incorporada, sem o nome da plataforma. Sem logo: cabeçalho neutro.

A execução no Render hospedado e o funcionamento com outras edições visuais de DISC ainda precisam de homologação.

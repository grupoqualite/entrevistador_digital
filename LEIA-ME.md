# Entrevistador Digital V9 | Piloto Render COM TRANSCRIÇÃO

Implementa entrevista por texto/áudio, logotipo opcional enviado pelo painel (PNG/JPG), roteiro segmentado em responsabilidades, hard skills e soft skills, registro de currículo, DISC e LinkedIn exportado, transcrição automática em fila após a entrevista e parecer em Competências Técnicas, Competências Comportamentais e Parecer de Recomendação, mediante revisão humana.

## Arquivos principais
- `render.yaml`: Blueprint para Render no plano EXECUÇÃO `1c-2g` com disco privado persistente de 2 GB.
- `Dockerfile.render`: instala faster-whisper e pré-baixa o modelo base multilíngue durante a compilação.
- `server.py`: API, entrevistas, fila de transcrição, armazenamento, documentos e relatórios.
- `static/`: interface do recrutador e do candidato.
- `GUIA_RENDER.md`: instruções passo a passo para publicar pelo GitHub/Render.
- `.gitignore`: protege dados locais e segredos de upload.

**Sem API paga por tokens.** A transcrição exige CPU/memória do plano Render; o score automático por modelo Ollama não está ativo nessa configuração. Não atribuir scores automáticos sem o motor de análise habilitado e validado.

Aviso: aplicação de piloto a ser homologada. Não considerar o sistema publicado até o Render confirmar deploy e os testes pelo celular. A integração automática do Google Drive permanece pendente.

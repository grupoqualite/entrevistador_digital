# Testes e limitações desta candidata a implantação

## Validado localmente
- [x] Sintaxe de Python e JavaScript.
- [x] Login, cadastro de vaga, geração de perguntas e convite individual com cliente de teste FastAPI.
- [x] Envio de respostas por texto e áudio (conteúdo de áudio fictício para testar o fluxo).
- [x] Conclusão da entrevista aciona fila de transcrição e registra o andamento no SQLite.
- [x] Transcrição simulada devolveu texto vinculado à pergunta e disponibilizado para análise.
- [x] Falha de reconhecimento impediu que conteúdo ausente fosse usado como evidência.
- [x] Organização de evidências e relatório no modo sem modelo conectado.
- [x] Upload de logotipo opcional PNG/JPG.

## Pendente de validação real
- [ ] Build Docker na infraestrutura do Render, incluindo download do modelo Whisper.
- [ ] Execução efetiva do faster-whisper com gravações reais em português.
- [ ] Tempo de transcrição e pico de RAM no plano 1c-2g.
- [ ] Gravação com microfone físico em Safari e Chrome, via HTTPS.
- [ ] Homologação de proteção de dados, backup e segurança antes de convidar candidatos reais.
- [ ] Avaliação semântica automática com Ollama ou motor equivalente: NÃO incluída no servidor Render de 2 GB.

Os testes de transcrição usaram um componente simulado para validar o fluxo. A precisão real do reconhecimento de voz não foi medida neste ambiente.

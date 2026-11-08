# Entrevistador Digital V9.6.5 | Somente texto

## Objetivo
Desativar respostas por áudio em novos convites e entrevistas, sem eliminar gravações históricas e sem exigir a instalação do faster-whisper no Render gratuito.

## Atenção antes de publicar
O Render Free permanece com armazenamento efêmero. Faça **backup externo** e confira o banco e os arquivos, especialmente as gravações antigas, antes do deploy. Uma nova implantação pode eliminar dados locais. **Não utilize dados reais de candidatos até haver persistência e controles adequados.**

## Atualização manual pelo GitHub
Substitua apenas estes arquivos no repositório, preservando os caminhos:

| Arquivo do pacote | Destino no repositório |
| --- | --- |
| server.py | `server.py` |
| static/interview.html | `static/interview.html` |
| static/interview.js | `static/interview.js` |
| static/index.html | `static/index.html` |
| static/app.js | `static/app.js` |
| requirements-render.txt | `requirements-render.txt` |

Não apague `engine.py`, banco de dados ou pastas de documentos. Não modifique a senha do Render.

Faça commit na branch conectada ao Render e use **Manual Deploy → Deploy latest commit**. Confira o commit mostrado nos logs.

## Conferência após publicar

1. Acesse `https://entrevistador-digital.onrender.com/api/health`: deve constar `"version": "9.6.5-text-only"`.
2. Abra um convite de teste. A entrevista só deve mostrar o campo de texto, sem opções de microfone ou gravação.
3. Digite respostas e conclua. O servidor deve registrar as respostas como `text`, sem gerar tarefa de transcrição.
4. No painel, as respostas aparecem para revisão e podem ser usadas na análise por critérios. O bloqueio de colagem é implementado na interface e não garante autoria em qualquer dispositivo.
5. Gravações de entrevistas anteriores permanecem disponíveis para reprodução e **transcrição manual**; a função automática de transcrição está desativada.

## Limites e segurança
- A atualização **não habilita análise semântica automática**; essa função continua exigindo um modelo de linguagem configurado. O painel permite revisão humana e minuta baseada em fontes disponíveis.
- O bloqueio de colagem é uma barreira de interface, não prova de autoria.
- Não há sincronização automática com Google Drive nem armazenamento persistente no Render Free.
- A interface não foi homologada no Safari do iPhone. Os testes automatizados do servidor foram executados localmente, mas o navegador automatizado desta sessão bloqueou a abertura de URLs de teste.

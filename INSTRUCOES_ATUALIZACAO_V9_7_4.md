# Entrevistador Digital V9.7.4: cruzamento técnico e comportamental

## Objetivo
Corrigir a elaboração de pareceres que desconsiderava notas ratificadas/retificadas e não cruzava suficientemente currículo, DISC, LinkedIn exportado e entrevista. A alteração abrange **Competências Técnicas**, **Competências Comportamentais** e a **síntese de recomendação**, mantendo a recomendação final sob responsabilidade do recrutador.

## Instalação no GitHub

**Antes de publicar, confirme que o backup atual está salvo e verificável.** O Render Free continua com armazenamento temporário.

Substituir estes arquivos no repositório existente, preservando os caminhos:

| Arquivo no ZIP | Caminho no GitHub |
| --- | --- |
| `server.py` | `/server.py` |
| `evidence_draft.py` | `/evidence_draft.py` |
| `behavioral_analysis.py` | `/behavioral_analysis.py` |
| `integrated_review.py` | `/integrated_review.py` (novo) |
| `static/app.js` | `/static/app.js` |
| `static/index.html` | `/static/index.html` |

Fazer commit na branch do serviço. No Render, acionar **Manual Deploy > Deploy latest commit**. Abrir `/api/health` no endereço da aplicação, aguardando `9.7.4-reviewed-evidence`.

## Comportamento depois da atualização

1. Na área **Entrevistas e dossiês**, selecionar um candidato.
2. Em **Análise técnica e revisão humana**, ratificar ou retificar as competências e salvar. A escrita das seções será atualizada quando ainda não houver redação editada/aprovada.
3. Verificar as três seções, inclusive **Competências Técnicas** e **Competências Comportamentais**. Na auditoria interna, revisar alertas e fontes associadas à análise.
4. Se a redação já tiver sido editada ou aprovada, o sistema **não sobrescreve o texto**. Ele sinaliza a necessidade de nova conferência e exige salvar novamente antes de aprovar.
5. Após conferência, utilizar **Aprovar e gerar dossiê PDF**.

## O que a correção NÃO faz

- Não instala um modelo semântico nem atribui notas automaticamente no Render Free. As notas são a avaliação preliminar efetiva, quando disponível, ou as notas ratificadas/retificadas por um humano.
- Não deduz comportamento a partir do DISC isoladamente. O instrumento entra como contexto e precisa de escala e leitura adequada.
- Não lê texto que esteja somente como imagem em PDF sem extração reconhecível. Se um arquivo não tiver texto, a fonte continuará indisponível para a síntese.
- Não cria armazenamento persistente. **Não use o Render Free como único repositório de dados reais**.

## Alterações técnicas auditadas

- A função de redação agora recebe notas validadas e fontes por critério.
- Currículo, entrevista e LinkedIn são usados como evidências distintas, evitando que uma palavra isolada sustente domínio de competência técnica.
- O DISC e o eventual comparativo são lidos de maneira complementar, com reconhecimento de nomes completos das dimensões e ressalvas sobre o instrumento.
- O texto externo não revela pesos, cálculo, histórico de notas, códigos de perguntas ou tecnologia utilizada.
- Uma nova avaliação humana atualiza a minuta ou marca o texto editado para revalidação, sem sobrescrita silenciosa.
- A auditoria de fontes e a identificação de divergências são internas ao painel.

## Testes efetuados

Testes automatizados locais: 6 aprovados, incluindo pontuação humana prevalecendo sobre a preliminar, ausência de nota indevida por DISC isolado, incompatibilidade entre critério e evidência, atualização do dossiê e preservação de texto editado. `app.js` passou pela verificação de sintaxe do Node.js e `server.py` foi importado com sucesso. A validação visual do navegador no Render publicado **não foi realizada** neste ambiente.

# Entrevistador Digital V9.7.3 | Parecer comportamental integrado

## Objetivo

A redação para clientes não descreve perguntas, códigos Q01/Q02, colagem de respostas nem importação de documentos. O parecer permanece nas três seções aprovadas:

1. Competências Técnicas
2. Competências Comportamentais
3. Parecer de Recomendação

A nova análise comportamental consulta **todas as atividades relatadas**, inclusive respostas a responsabilidades e hard skills, e considera a trajetória profissional como **contexto**, sem presumir que a atividade exercida prove uma competência pessoal. O DISC funciona como **referência complementar**, com interpretação condicionada à escala e às informações realmente presentes no laudo. Não são atribuídas notas automáticas.

O gerador é baseado em regras e não equivale a um modelo semântico completo. Sempre confira os fatos e reescreva o que exigir interpretação profissional adicional antes de enviar ao cliente. Não pressupõe resultados, personalidade, estabilidade emocional nem liderança sem evidência contextual.

## Atualização do repositório GitHub

Substitua **somente** os arquivos do ZIP, mantendo os caminhos:

- `server.py` na raiz
- `evidence_draft.py` na raiz
- `behavioral_analysis.py` na raiz (**arquivo novo**, obrigatório)
- `static/index.html`
- `static/app.js`
- `static/interview.html`

Não substitua o banco, as pastas de dados ou os arquivos de candidatos. A atualização preserva o login, o cadastro de usuários, a restauração de backups, o fluxo de respostas apenas por texto e a aprovação do PDF.

Faça o commit na branch implantada no Render e execute **Manual Deploy > Deploy latest commit**. Acesse `/api/health` e confirme `9.7.3-behavior-integrated`. O número do painel deve coincidir.

## Atualizar um parecer anteriormente preparado

1. Selecione o candidato em **Entrevistas e dossiês**.
2. Clique em **Preparar novamente o texto a partir das fontes**.
3. Confirme a substituição dos textos **somente nos campos de edição**. Uma aprovação anterior não é alterada automaticamente.
4. Confira as três seções. Ajuste fatos, interpretação do DISC e recomendação.
5. Clique em **Aprovar e gerar dossiê PDF** para salvar, aprovar e baixar a nova versão. A aprovação exige confirmação explícita.

O sistema impedirá salvar/aprovar novos pareceres com frases operacionais antigas como “na resposta Q02” e “no perfil profissional exportado”. É necessário reescrever a minuta, e não apenas remover a expressão em PDF.

## Validação

23 testes automatizados aprovados localmente, inclusive geração de PDF, proibição de códigos de perguntas no texto externo, recuperação de condutas relatadas em critérios técnicos, cautela com indicadores numéricos do DISC, aprovação direta e integridade de autenticação.

**Limitações:** a qualidade das interpretações automáticas ainda requer homologação em candidatos autorizados; a hospedagem gratuita do Render permanece sem armazenamento durável. O uso operacional com dados pessoais exige persistência e controle de acesso adequados.

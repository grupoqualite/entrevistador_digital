# Qualité Entrevistar Digital | Versão 9.7.7

**Origem:** pacote completo da versão 9.7.5 fornecido pelo usuário em 15/11/2026. Esta atualização não usa a versão 9.7.6 como base.

## Finalidade

Melhorar a elaboração do parecer de entrevista, preservando as três áreas de entrega (**Competências Técnicas**, **Competências Comportamentais** e **Parecer de Recomendação**) e a decisão do recrutador.

## Modificações realizadas

1. `narrative_upgrade.py` (novo): síntese baseada em trechos concretos de currículo, histórico textual do LinkedIn, relato profissional transcrito e respostas do questionário. O DISC é interpretado como dado complementar da análise comportamental. A saída mantém rastreabilidade interna de trechos, por origem.
2. `evidence_draft.py`: integração do novo módulo de redação após a auditoria de evidências existente. Exclui rótulos editoriais provisórios da redação ao cliente, inclusive “Novo critério, inserir origem e competência”. Preserva o fluxo de revisão humana.
3. `server.py`: corrige a consulta que usava `career_narrative_text` sem selecionar esse campo durante a revisão. Atualiza `/api/health` para versão `9.7.7-parecer-qualite` e build `qualite-parecer-evidencias-5-fontes`.
4. `static/qualite-marca-horizontal.png`: logotipo institucional enviado pelo usuário. O arquivo é **exclusivo da interface** e não substitui automaticamente o logo personalizado do parecer.
5. `static/index.html`, `static/styles.css`, `static/app.js`: logotipo Qualité no topo e na barra lateral, ajustes de legibilidade e indicadores de disponibilidade das cinco fontes no painel, incluindo o questionário respondido.
6. `tests/test_qualite_977.py`: testes de origem das evidências, PDF com três seções, marca independente e revisão humana após fornecimento da transcrição.

## Como atualizar manualmente no GitHub e Render

1. **Antes de começar**, acesse o painel atual e faça o backup do banco e anexos. Confira no ZIP de backup `dados.sqlite3` e a pasta `arquivos/`. Guarde o arquivo em local privado. Não confunda o backup de dados com este pacote de código.
2. No GitHub, abra o repositório **que está ligado ao serviço Render em produção**. Preserve os arquivos e variáveis de ambiente da implantação atual.
3. Descompacte este pacote em seu computador. Substitua no repositório os arquivos de mesmo caminho, mantendo exatamente a estrutura de pastas. Envie também os **novos** arquivos `narrative_upgrade.py` e `static/qualite-marca-horizontal.png`.
4. Faça commit das alterações na branch configurada no Render, normalmente `main`.
5. No Render, selecione o serviço já existente e clique **Manual Deploy → Deploy latest commit**. Não crie outro serviço nem altere o comando de inicialização.
6. Depois do deploy, acesse `https://entrevistador-digital.onrender.com/api/health` (ou o domínio real do seu serviço). Verifique `"version":"9.7.7-parecer-qualite"` e `"build":"qualite-parecer-evidencias-5-fontes"`.
7. Entre no painel, confira a marca Qualité na interface e teste com candidato **fictício**: currículo, DISC, LinkedIn exportado, respostas escritas e transcrição. Prepare a minuta, revise os três campos, escolha o logotipo do parecer e gere uma prévia PDF.
8. Aprove o documento somente depois de conferir as evidências. O fluxo de aprovação humana continua obrigatório.

## O que permanece inalterado

- Usuários administradores/recrutadores, autenticação e alteração de senha.
- Vagas, questionários, convites, respostas somente por texto e bloqueios de colagem já existentes.
- Importação e recuperação de documentos; leitura de DISC individual e comparativo Recrutei.
- Backup/restauração no formato da versão 9.7.5.
- Logo do PDF selecionável em **Entrevistas e dossiês > Identidade visual do parecer**. Ele usa `/api/brand/logo` e o arquivo `branding/logo.png` no diretório de dados, separado do logotipo da interface.
- Notas 0–4, índice de aderência e julgamento de avanço sob controle humano, sem aprovação ou reprovação automática.

## Limitações relevantes

- **Não foi implantado um modelo generativo no Render.** A composição textual desta versão usa seleção e combinação de evidências por regras. Com documentos e exemplos detalhados, ela produz textos mais específicos; não equivale a uma redação contextual de um analista humano e continua exigindo revisão.
- O LinkedIn é avaliado **somente pelo texto ou PDF fornecido**; o link por si só não disponibiliza o perfil para análise automática.
- A transcrição da apresentação deve ser enviada já em texto, PDF ou DOCX. Esta versão não reintroduz áudio.
- A interface foi verificada em código, e as rotas foram exercitadas por cliente HTTP de teste. Uma inspeção visual automatizada no navegador foi bloqueada por política do ambiente; a verificação visual final depende do deploy.
- Não foi executado deploy na sua conta Render ou GitHub. **Não há homologação em produção.**
- Na infraestrutura Render sem disco persistente, atualizações/reinicializações podem apagar arquivos e banco locais. Faça backup antes do deploy e configure armazenamento persistente privado antes de trabalhar com dados pessoais reais.

## Verificações realizadas

- Compilação de todos os módulos Python.
- Verificação de sintaxe do JavaScript (`node --check`).
- **16 testes automatizados aprovados**, incluindo fluxos de login, vagas, entrevista, transcrição, backup, PDF, aprovação humana e aderência aos cinco tipos de fonte.
- Emissão de PDF de exemplo fictício com três seções, aberto e renderizado localmente.
- Rota de saúde respondeu com versão e build esperados.

## Estrutura para upload

Este é um **pacote completo de código-fonte**, com arquivos na raiz do ZIP (`server.py`, `engine.py`, `static/`, `tests/` etc.), não uma pasta adicional dentro do ZIP. Copie o conteúdo para a raiz do repositório GitHub da versão 9.7.5.

# Qualité Entrevistar Digital | V9.7.5 consolidada

## O que foi incorporado

1. **Perguntas situacionais:** cada questão gerada por regras preserva o requisito da vaga, pede uma situação real de trabalho e orienta o candidato a utilizar experiência semelhante quando não tiver vivenciado o cenário exatamente. Não estimula inventar situações. A orientação também aparece durante toda a entrevista.
2. **Relato profissional complementar:** o recrutador pode cadastrar a transcrição de um resumo profissional narrado pelo candidato, colando o texto ou anexando PDF/DOCX/TXT no cadastro ou na área de dossiês. O arquivo de áudio original **não é gravado nem transcrito** nesta versão. A transcrição é interpretada como relato e fonte complementar, não como comprovação independente.
3. **Identidade Qualité:** nome Qualité Entrevistar Digital, paleta creme/oliva/carvão inspirada no Qualité CRM, navegação lateral no desktop, layout responsivo no celular. O logotipo destinado ao parecer permanece configurável e não é substituído pela marca da plataforma no documento do cliente.
4. **Aviso de teste removido da interface:** removida a faixa de aviso das telas do painel e do candidato; o risco de armazenamento temporário continua explicitado na administração de backups.
5. **Compatibilidade:** mantém contas de Administrador e Recrutador, restauração de backup, DISC Recrutei, entrevistas exclusivamente digitadas e parecer em três seções.

## Atualização no GitHub e Render (manual, sem Blueprint)

1. No serviço atual, baixe o backup e confirme a presença de `dados.sqlite3` e de `arquivos/` no ZIP. Guarde em uma pasta privada fora do Render.
2. Extraia o pacote **Atualização GitHub** e substitua seus arquivos respeitando a estrutura de pastas. O repositório pode continuar privado.
3. Faça Commit na branch conectada ao Render, geralmente `main`.
4. No Render, use **Manual Deploy → Deploy latest commit**. Não altere as credenciais administrativas que já funcionam.
5. Consulte `https://entrevistador-digital.onrender.com/api/health`. O campo `version` continua `9.7.5-disc-brand` para compatibilidade e o campo `build` deve ser `qualite-situacional-relato-profissional`.
6. Em **Vagas e roteiro**, crie uma nova vaga com descrição e confira o questionário situacional. Vagas com convites já emitidos preservam o roteiro anterior. O candidato verá, em todas as entrevistas, a orientação geral para trazer experiências similares.
7. Em **Candidatos e convites**, anexe uma transcrição pronta opcional. Em **Entrevistas e dossiês**, use o formulário de relato profissional para complementar uma candidatura existente ainda não revisada ou aprovada e atualizar a minuta.

## Limites relevantes

- A geração de perguntas utiliza regras contextuais associadas à descrição da vaga, não um modelo generativo em execução no Render Free. As perguntas requerem revisão pelo recrutador.
- A transcrição do relato profissional precisa estar **pronta**. O upload de áudio e o Whisper continuam desativados; a nova função não reintroduz gravação ou transcrição automática.
- **A remoção do aviso visual não altera a infraestrutura.** O Render Free sem disco persistente continua sujeito à perda de banco e anexos após suspensão ou reinicialização. Backups manuais não equivalem a persistência contínua. Não considerar o sistema homologado para dados reais sem armazenamento externo privado e mecanismos de recuperação testados.
- A análise documental continua dependente da qualidade do material e da revisão humana; o sistema não aprova nem reprova candidatos automaticamente.

## Testes locais executados

- Importação e inicialização da aplicação, autenticação administrativa e diagnóstico de compilação.
- Geração de 11 perguntas para a vaga exemplo, todas com orientação de vivência equivalente.
- Cadastro de candidato e transcrição complementar digitada.
- Atualização posterior do relato por texto e DOCX com confirmação de persistência no SQLite local.
- Conclusão de entrevista por texto, preparação das três seções e emissão de prévia PDF.
- Verificação da presença da marca e da remoção das faixas de teste.
- Compilação de módulos Python e verificação sintática do JavaScript.

**Pendente:** teste visual completo do navegador do usuário e implantação efetiva no Render. O navegador automatizado neste ambiente bloqueou a navegação localhost; a API foi testada por cliente HTTP local.

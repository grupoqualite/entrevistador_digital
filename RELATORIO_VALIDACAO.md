# Validação da atualização consolidada V9.7.5

**Escopo:** somente leitura dos dois formatos DISC da Recrutei e identidade visual exclusiva do PDF.

- Parser do comparativo de 22 páginas: identificou os quatro segmentos e a classificação de perfil.
- Parser gráfico do DISC individual de 3 páginas: D5/I1/S7/C4 no exemplar fornecido; o resultado coincide com o comparativo.
- Uma divergência fabricada para teste foi destacada, em vez de substituída silenciosamente.
- A inclusão posterior do currículo não apagou os dados DISC existentes.
- A releitura do PDF individual armazenado foi concluída por operação autenticada.
- Nos testes unitários, PDFs do cliente com e sem imagem não apresentaram o nome do aplicativo.

**Limites:** não foi feita homologação do Render de produção; o parser geométrico não equivale a OCR integral do documento de três páginas. Não foram adicionados modelos de IA pagos.

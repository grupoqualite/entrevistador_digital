# Auditoria do gerador V9.7.3 e correções V9.7.4

| Achado | Consequência na versão antiga | Correção |
| --- | --- | --- |
| `draft_from_sources` ignorava `auto_score`, `human_score` e `review_decision` | Nota humana não influenciava as três seções do parecer | Integração por critério, usando avaliação humana quando existente |
| A avaliação de currículo/LinkedIn era majoritariamente temática | Menção documental isolada podia parecer domínio técnico | Verificação conservadora de pertinência e sinalização de fontes insuficientes |
| `disc_paragraph` esperava chaves `D`, `I`, `S`, `C`, mas `disc_summary` produzia nomes completos | Dimensões informadas do DISC não eram usadas corretamente | Reconhecimento de ambas as formas e leitura textual qualificada |
| Comparativo DISC vinha após laudo longo | Trechos relevantes podiam ser descartados pelo corte inicial de texto | Prioriza parte do comparativo na leitura, sem inventar uma interpretação |
| `update_review` atualizava pontuação, mas não regenerava a minuta | Dossiê podia ficar defasado após retificação | Atualização automática apenas de conteúdo não editado e indicação de revalidação quando necessário |
| Ausência de quadro de controle das fontes utilizadas | Recrutador não conseguia identificar divergência pontuação/evidência | Trilha e alertas internos, sem exposição no PDF do cliente |

## Salvaguardas

A evidência encontrada nos documentos é **declaração profissional**, não comprovação externa. A nota retificada pode orientar a narrativa, mas não substituir relato, resultado ou registro contextualizado. Não se presume adequação, caráter eliminatório nem perfil psicológico por palavras isoladas. O parecer de recomendação permanece dependente da avaliação e da confirmação expressa do recrutador.

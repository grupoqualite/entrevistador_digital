"""Gerador de entrevistas por competência: baseado em evidências da descrição.

Sem API de inferência: perguntas contextualizadas por atividade identificada.
Nenhuma ferramenta/requisito ausente da vaga é acrescentado como exigência.
O recrutador revisa e aprova as perguntas antes do convite.
"""
from __future__ import annotations
import re
import unicodedata

STOP = set('a o as os um uma uns umas para por com sem que de da do das dos em no na nos nas ao aos e ou se sua seu seus suas como quando onde qual quais foi foram sobre tem ter tinha isso esse esta este está ser são mais menos cada todos todas assim forma meio caso dado dados entre mas porque ainda também voce você precisar experiencia necessario necessaria requisito atuar conhecimento habilidade dominio desejavel capacidade possuir atividades responsabilidades profissionais desejado minimo anos'.split())

def norm(s: str) -> str:
    return ''.join(x for x in unicodedata.normalize('NFKD',s or '') if not unicodedata.combining(x)).lower()

def tokens(s: str) -> set[str]:
    return {x for x in re.findall(r'[a-z0-9]{3,}',norm(s)) if x not in STOP}

def clean(s: str) -> str:
    return re.sub(r'\s+',' ',s or '').strip(' \u2022-\t:;')

# Palavras normalizadas para reduzir erros de acentuação.
SOFT = re.compile(r'comunic|colabora|trabalho em equipe|autonomi|iniciativ|proativ|resilien|empati|escuta ativa|flexibil|adaptab|organiz|atencao aos detalhes|disciplina|etica|lideran|gestao de conflitos|senso critic|pensamento analit|criativ|orienta.{0,12}resultad|soluc.{0,12}problema|inteligencia emocional|relacionamento interpessoal|comprometimento|assertiv|capacidade de aprender|postura|gestao do tempo',re.I)
HARD = re.compile(r'\bexcel\b|\bpower ?bi\b|\bsql\b|\bpython\b|\bcrm\b|\berp\b|sap|totvs|pipedrive|salesforce|hubspot|google ads|metas ads|\biso\b|\bnr ?\d+\b|\bcrea\b|autocad|revit|wordpress|photoshop|canva|capcut|prospec|outbound|inbound|qualifica|funil de vendas|pipeline|analise de dados|relatorio|gestao financeira|contas a pagar|contas a receber|concili|faturamento|tribut|cota[cç]|logist|gestao de projetos|compliance|auditoria|legisla|vendas consultivas|negocia[cç]|fechamento|infraestrutura|paviment|drenagem|saneamento|recrut|selecao|entrevista por compet|obras|or[cç]amento|cronograma|planejamento de midia|trafego pago',re.I)
ACTION = re.compile(r'^(executar|realizar|conduzir|gerenciar|coordenar|desenvolver|implantar|implementar|acompanhar|planejar|controlar|analisar|monitorar|elaborar|apresentar|atender|prospectar|negociar|efetuar|organizar|produzir|operar|garantir|apurar|validar|construir|criar|vender|fechar|captar|prestar|registrar|lidar|manter|identificar|solucionar|avaliar|participar|atuar|responsavel|fazer|gestao de|apoiar|supervisionar|conferir)\b',re.I)
DIFF = re.compile(r'\bdiferencial\b|\bdesejavel\b|\bplus\b|\bpreferencial\b|\bnao obrigatorio\b',re.I)
LOGISTICS = re.compile(r'presencial|hibrido|remoto|disponibilidade|contratacao|\bclt\b|\bpj\b|sabado|turno|jornada|horario|\bcnh\b|viagens|residir|localizacao',re.I)
HEADERS = [
 (re.compile(r'^(?:responsabilidades|atribuicoes|atividades|escopo da funcao|o que (?:voce )?fara|no dia a dia|principais atividades|entregas esperadas|rotina|principais responsabilidades)$'),'responsabilidade'),
 (re.compile(r'^(?:requisitos tecnicos|conhecimentos tecnicos|habilidades tecnicas|hard skills|ferramentas|tecnologias|formacao e experiencia|experiencia tecnica)$'),'hard'),
 (re.compile(r'^(?:competencias comportamentais|perfil comportamental|soft skills|habilidades comportamentais|caracteristicas pessoais|perfil desejado|comportamentos esperados)$'),'soft'),
 (re.compile(r'^(?:diferenciais|desejaveis|diferencial|sera um diferencial|sera considerado um diferencial)$'),'diferencial'),
 (re.compile(r'^(?:requisitos|qualificacoes|o que esperamos|o que buscamos|experiencia exigida|exigencias|requisitos obrigatorios)$'),'requisito'),
]

# Critérios específicos. Cada pergunta investiga como o candidato executou uma atividade,
# com evidências de método e resultado. Os termos específicos (ex.: CRM) só são usados
# quando aparecem no requisito da vaga.
PATTERNS = [
 (r'concilia', 'Conciliação e fechamento de valores', 'Descreva uma conciliação que realizou: como comparou os registros, identificou diferenças e comprovou que os valores finais estavam corretos?', 'Origem dos dados, conferência, tratamento de divergências e evidência de fechamento.'),
 (r'contas a pagar|contas a receber', 'Rotinas de pagamentos e recebimentos', 'Explique uma rotina de contas a pagar ou a receber que executou diretamente. Como controlava vencimentos, aprovações, baixas e divergências?', 'Frequência, controles, tratamento de exceções e indicadores de atraso.'),
 (r'fluxo de caixa|tesouraria', 'Fluxo de caixa', 'Conte como preparou e acompanhou um fluxo de caixa. Quais informações reuniu, como projetou entradas e saídas e que decisões apoiou?', 'Premissas, conferências, previsão e impacto na decisão.'),
 (r'coordenar.{0,45}(?:prestadores|fornecedores|equipes)|prestadores e fornecedores', 'Coordenação de prestadores', 'Conte como coordenou uma entrega com profissionais ou fornecedores externos. Como alinhou escopo e prazos, acompanhou pendências e cobrou a execução?', 'Planejamento, comunicação, cobrança, registro e resultado.'),
 (r'compras|suprimentos|cota[cç]|negociacao com fornecedores', 'Compras e fornecedores', 'Relate uma aquisição sob sua responsabilidade. Como levantou a necessidade, comparou propostas, negociou e verificou prazo, custo e qualidade da entrega?', 'Critérios de comparação, negociação, riscos e resultado.'),
 (r'prospe[cç]|outbound|captacao de clientes', 'Prospecção ativa', 'Descreva uma campanha ou rotina de prospecção que você executou. Como escolheu o público, definiu os canais, organizou a cadência e mediu as oportunidades geradas?', 'Público, cadência, taxa de resposta, reuniões e participação direta.'),
 (r'qualifica[cç].{0,12}lead|\blead[s]?\b', 'Qualificação de oportunidades', 'Conte sobre um contato que chegou ao seu funil de vendas. Quais perguntas fez para qualificar a oportunidade e como decidiu avançar ou desqualificar?', 'Critérios objetivos de qualificação e decisão comercial.'),
 (r'vendas? consultiv|diagnostico comercial|spin selling|\bbant\b', 'Venda consultiva', 'Relate uma venda consultiva que conduziu. Como investigou a necessidade, ajustou a proposta de valor e verificou se a solução atendia ao cliente?', 'Diagnóstico, argumentação, papel pessoal e resultado.'),
 (r'fechamento|\bcloser\b|negocia[cç].{0,15}comercial|objec', 'Negociação e fechamento', 'Conte sobre uma negociação difícil que você conduziu até a decisão. Qual objeção surgiu, como a trabalhou e qual foi o resultado?', 'Objeção, postura, técnica de negociação e conversão.'),
 (r'\bcrm\b|\bpipeline\b|funil de vendas|pipedrive|salesforce|hubspot', 'Gestão do funil e CRM', 'Explique como organizava oportunidades no CRM, atualizava etapas e programava os próximos contatos. Dê um caso em que esses registros mudaram sua decisão comercial.', 'Sistema utilizado, rastreabilidade, priorização e disciplina de follow-up.'),
 (r'cursos|educa[cç][aã]o executiva|p[oó]s.gradua[cç][aã]o|formacoes profissionais', 'Comercialização de educação', 'Você já comercializou cursos ou formações? Caso tenha, descreva como apresentou o valor educacional, tratou objeções e acompanhou a matrícula. Caso não tenha, conte uma venda comparável.', 'Experiência direta ou competência transferível; diferencial não eliminatório.'),
 (r'\bmetas?\b(?! ads)|\bkpi\b|indicadores? de convers', 'Gestão de metas e indicadores', 'Escolha uma meta pela qual foi responsável. Qual era o indicador, qual resultado alcançou no período e o que ajustou quando percebeu um desvio?', 'Meta, período, resultado e papel efetivo.'),
 (r'\bexcel\b|planilhas?|\bpower ?bi\b', 'Análise em planilhas e painéis', 'Descreva uma planilha ou painel que desenvolveu ou manteve. Quais dados reuniu, que fórmulas ou medidas utilizou e como conferiu a confiabilidade do resultado?', 'Nível real de domínio, lógica dos cálculos e validação.'),
 (r'\berp\b|\bsap\b|totvs', 'Sistemas de gestão', 'Explique um processo que realizou no sistema de gestão utilizado. Que registros produziu, que integrações verificou e como corrigiu uma inconsistência?', 'Sistema efetivamente utilizado, autonomia e controles.'),
 (r'orcamento|composicao de custos|quantitativos', 'Orçamentos e custos', 'Conte como elaborou ou acompanhou um orçamento. Como levantou os quantitativos ou premissas, verificou custos e tratou desvios entre previsto e realizado?', 'Critérios de orçamento, ferramentas, controle e desvio.'),
 (r'cronograma|planejamento de obra|\bprazo', 'Cronograma e prazos', 'Relate um projeto ou obra em que uma etapa atrasou. Como identificou dependências, reorganizou o cronograma e comunicou os impactos?', 'Sequência crítica, responsáveis, replanejamento e resultado.'),
 (r'gestao de obras|gerenciar.{0,25}obras|acompanhar obras|fiscaliza[cç]|acompanhamento de obras|canteiro', 'Gestão e fiscalização de obras', 'Descreva uma obra que acompanhou diretamente. Como conferiu a execução em relação ao projeto, cobrou prestadores e registrou qualidade e pendências?', 'Papel na obra, método de fiscalização e ações corretivas.'),
 (r'projeto executivo|leitura de projeto|\bbim\b|\brevit\b|autocad', 'Interpretação de projetos', 'Apresente um caso em que interpretou ou compatibilizou projetos antes da execução. Que incompatibilidade encontrou, como a resolveu e como registrou a alteração?', 'Leitura técnica, compatibilização, decisão e documentação.'),
 (r'auditoria|nao conformidade|iso 9001|iso 14001|iso 45001', 'Auditoria e conformidade', 'Descreva uma auditoria ou não conformidade em que atuou. Qual requisito verificou, que evidências coletou e como acompanhou a eficácia das ações?', 'Requisito, evidência objetiva, ação e verificação.'),
 (r'wordpress|canva|photoshop|capcut|edicao de conteudo', 'Ferramentas digitais e produção', 'Descreva uma peça ou página que produziu usando as ferramentas citadas na vaga. O que realizou sozinho, que recursos utilizou e como validou a entrega?', 'Ferramentas utilizadas, autonomia e qualidade da entrega.'),
 (r'trafego pago|google ads|meta[s]? ads|campanhas pagas', 'Gestão de mídia paga', 'Descreva uma campanha paga que gerenciou. Como definiu público, orçamento, criativos e indicadores e quais ajustes realizou para melhorar o desempenho?', 'Objetivo, plataforma, orçamento, métricas e otimização.'),
 (r'\bcopy\b|conteudo|redes sociais|posts?\b', 'Produção de conteúdo', 'Conte como planejou uma peça ou sequência de conteúdo para um público definido. Como escolheu a mensagem, executou a publicação e avaliou o resultado?', 'Briefing, produção, canais e desempenho.'),
 (r'recrutamento|selecao|\bhunting\b|triagem de candidatos', 'Recrutamento e seleção', 'Descreva uma seleção que conduziu. Como alinhou requisitos com o gestor, buscou candidatos, avaliou evidências e documentou a recomendação?', 'Critérios, técnicas de seleção, evidências e comunicação ao gestor.'),
 (r'\bsql\b|\bpython\b|desenvolvimento de software|api[s]?\b', 'Implementação e dados', 'Explique uma entrega técnica que desenvolveu. Que problema resolveu, quais tecnologias utilizou, como testou e como comprovou o funcionamento?', 'Participação pessoal, implementação, testes e resultado.'),
 (r'atendimento ao cliente|atender clientes|relacionamento com clientes|suporte ao cliente', 'Atendimento e relacionamento', 'Conte sobre um atendimento complexo que assumiu. Como identificou a demanda, definiu prioridades e confirmou que o cliente recebeu a solução?', 'Diagnóstico, encaminhamento, retorno e resultado.'),
 (r'lideran[cç]|gestao de equipe|coordenar equipe', 'Coordenação de equipes', 'Descreva uma entrega coordenada por você. Como distribuiu responsabilidades, acompanhou o trabalho e tratou um desvio de desempenho?', 'Delegação, acompanhamento, feedback e entrega.'),
 (r'autonom|iniciativa|proativ', 'Autonomia e iniciativa', 'Conte uma situação concreta em que precisou agir sem receber orientação imediata. Como avaliou alternativas, decidiu e assumiu a responsabilidade pelo resultado?', 'Decisão, limites de autonomia, risco e consequência.'),
 (r'escuta ativa|comunica|comunicativ|relacionamento interpessoal', 'Comunicação e escuta', 'Relate uma situação profissional em que precisou adaptar a comunicação a alguém com uma necessidade ou visão diferente. O que ouviu, como respondeu e qual foi o desfecho?', 'Escuta, clareza, adaptação e resultado observado.'),
 (r'resili|trabalho sob pressao|pressao por resultados', 'Resiliência e pressão', 'Descreva um momento em que houve um contratempo ou pressão relevante na sua rotina. Como reorganizou as ações e preservou a qualidade da entrega?', 'Situação, regulação, priorização e recuperação.'),
 (r'organiza|gestao do tempo|planejamento|prioriz', 'Organização e prioridades', 'Conte uma situação em que precisou administrar várias entregas simultâneas. Como definiu prioridades, acompanhou prazos e tratou imprevistos?', 'Método, prioridades, monitoramento e cumprimento.'),
 (r'colabora|trabalho em equipe', 'Colaboração', 'Descreva uma entrega que exigiu colaboração entre diferentes profissionais. Como dividiu responsabilidades, tratou divergências e contribuiu para o resultado?', 'Atuação pessoal, articulação e resolução de impasses.'),
 (r'atencao aos detalhes', 'Atenção aos detalhes', 'Conte uma situação em que identificar um detalhe evitou um erro ou retrabalho. Como percebeu o problema, verificou a informação e corrigiu a entrega?', 'Checagem, prevenção de falhas e consequência da atenção ao detalhe.'),
 (r'criativ', 'Criatividade aplicada', 'Conte uma ocasião em que precisou encontrar uma solução criativa para um problema de trabalho. Como construiu a ideia, testou a solução e verificou o resultado?', 'Problema concreto, alternativas, execução e impacto.'),
 (r'adaptab|flexibil|mudan[cç]', 'Adaptação a mudanças', 'Conte uma situação em que uma mudança inesperada exigiu revisar seu plano. O que mudou na sua atuação e como avaliou o resultado?', 'Resposta à mudança, decisões e aprendizagem.'),
 (r'negocia[cç].{0,10}conflit|gestao de conflitos|assertiv', 'Gestão de conflitos', 'Conte um conflito profissional que precisou enfrentar. Como apresentou sua posição, ouviu as partes e chegou a um encaminhamento?', 'Assertividade, escuta, decisão e efeito.'),
]

# Só consideramos uma pergunta fundamentada quando existe fonte da vaga.
HEADER_MARKER = re.compile(r'^(?:\s*[-•*]\s*)?(?:[0-9]+[.)]\s*)?')
IGNORE = re.compile(r'^(?:sobre a empresa|sobre nos|beneficios|oferecemos|o que oferecemos|remuneracao|salario|carga horaria|sobre a vaga|inscricao|inscreva.se|como se candidatar)(?:\s*:|$)')

def fragments(jd:str) -> list[dict]:
    context=None; output=[]
    for line_no, raw in enumerate((jd or '').replace('\r','\n').split('\n'),1):
        line=clean(HEADER_MARKER.sub('',raw))
        if not line:continue
        normal=norm(line).strip(' :.;')
        header=next((t for pat,t in HEADERS if pat.fullmatch(normal)),None)
        if header:context=header;continue
        if IGNORE.match(normal):context=None;continue
        if context is None and line_no<=2 and len(line)<105 and re.match(r'^(?:gestor|analista|assistente|executivo|comprador|desenvolvedor|engenheiro|arquiteto|vendedor|auxiliar|closer|estagio|tecnico)\b',normal):
            continue  # título da vaga, não é competência para entrevista
        # Seções com título e conteúdo na mesma linha (comuns após extração de DOCX/PDF)
        match=re.match(r'^([^:]{3,50}):\s+(.{12,})$',line)
        if match:
            maybe=norm(match.group(1))
            label=next((t for pat,t in HEADERS if pat.fullmatch(maybe)),None)
            if label:context=label;line=match.group(2)
        # Evita cabeçalho solto, informações sobre pagamento e marketing institucional
        if (len(line)<8 and not (HARD.search(normal) or SOFT.search(normal))) or len(line)>2500:continue
        parts=[line]
        if len(line)>320 or re.search(r'\.\s+[A-ZÀ-Ú]',line):parts=[clean(p) for p in re.split(r'(?<=[.;])\s+(?=[A-Za-zÀ-ÿ])',line) if clean(p)]
        for part in parts:
            # listas explícitas de competências separadas por vírgulas, mas não dividir frases de atividade
            subparts=[part]
            if context in ('hard','soft','diferencial','requisito') and len(part)<230 and (',' in part or ';' in part):
                xs=[clean(x) for x in re.split(r'[,;]',part) if len(clean(x))>=6]
                if 1<len(xs)<=8:subparts=xs
            # "Excel e ERP" e "resiliência e escuta ativa" são critérios distintos;
            # só divide se os dois lados são competências reconhecíveis.
            if context in ('hard','soft','diferencial','requisito'):
                separated=[]
                for item in subparts:
                    halves=re.split(r'\s+e\s+',item,maxsplit=1,flags=re.I)
                    if len(halves)==2 and len(halves[0])>=3 and len(halves[1])>=3 and all((HARD.search(norm(x)) or SOFT.search(norm(x))) for x in halves):
                        separated.extend(halves)
                    else:separated.append(item)
                subparts=separated
            for value in subparts:
                t=norm(value)
                # Informação de treinamento/ausência de experiência não é soft skill.
                if re.search(r'\b(?:nao (?:e|sera) obrigatori[ao]|empresa oferece treinamento|nao exigimos experiencia)\b',t):continue
                if (len(value)<8 and not (HARD.search(t) or SOFT.search(t))) or IGNORE.match(t):continue
                differential=context=='diferencial' or bool(DIFF.search(t))
                if context=='responsabilidade':cat='responsabilidade'
                elif context=='soft':
                    # Texto extraído de PDF pode fundir responsabilidades numa seção comportamental.
                    cat='responsabilidade' if re.search(r'medicament|preparac.{0,10}pedidos|imprimir ficha|realizar entrega|conferir produto',t) else 'soft'
                elif context=='hard':cat='hard'
                elif context=='diferencial':cat='soft' if SOFT.search(t) and not HARD.search(t) else 'hard'
                elif context=='requisito':cat='soft' if SOFT.search(t) and not HARD.search(t) else 'hard'
                elif ACTION.match(t):cat='responsabilidade'
                elif SOFT.search(t) and not HARD.search(t):cat='soft'
                elif HARD.search(t):cat='hard'
                elif LOGISTICS.search(t):cat='logistica'
                else:continue
                output.append({'origin':value[:500], 'line':line_no,'category':cat,'kind':'diferencial' if differential else cat,'is_differential':differential})
    # Não repetir mesmo critério na mesma categoria
    uniq=[]
    for r in output:
        tk=tokens(r['origin'])
        if not tk:continue
        if any(r['category']==p['category'] and len(tk&tokens(p['origin']))/max(1,min(len(tk),len(tokens(p['origin']))))>.85 for p in uniq):continue
        uniq.append(r)
    return uniq

def _pattern(entry):
    phrase=norm(entry['origin'])
    # Prioridades para padrões mais específicos (e categorias comportamentais explícitas)
    if entry['category']=='soft':
        prefer=['Autonomia e iniciativa','Comunicação e escuta','Resiliência e pressão','Organização e prioridades','Colaboração','Adaptação a mudanças','Gestão de conflitos','Coordenação de equipes']
    elif entry['category']=='responsabilidade':
        prefer=['Gestão e fiscalização de obras','Cronograma e prazos','Orçamentos e custos','Prospecção ativa','Qualificação de oportunidades','Venda consultiva','Negociação e fechamento','Gestão do funil e CRM']
    else:prefer=[]
    matches=[]
    for patt,focus,q,evidence in PATTERNS:
        if re.search(patt,phrase,re.I):matches.append((focus,q,evidence))
    return next((m for p in prefer for m in matches if m[0]==p),matches[0] if matches else None)

def make_question(entry:dict,cv:str='',idx:int=0)->dict:
    origin=entry['origin'];cat=entry['category'];detected=_pattern(entry)
    if detected:
        focus,question,evidence=detected
    else:
        # Fallback que mantém o objeto do requisito, não perguntas vazias do tipo 'conte sobre isso'.
        subject=clean(re.sub(r'^(?:experiencia (?:com|em)|dominio (?:de|em)|conhecimento (?:de|em)|atuar (?:com|em)|responsavel por|realizar|executar|conduzir|desenvolver|gerenciar|acompanhar|elaborar|controlar|organizar|garantir)\s+','',origin,flags=re.I))[:150]
        if cat=='responsabilidade':
            focus='Execução da responsabilidade';question=f'Na atividade de {subject}, descreva uma entrega que você realizou: quais etapas executou pessoalmente, como verificou a qualidade e que resultado obteve?'
            evidence='Atividades executadas, papel real, qualidade e resultado.'
        elif cat=='soft':
            focus='Comportamento em situação real';question=f'Em uma situação de trabalho que exigiu {subject}, como você agiu, qual dificuldade encontrou e que efeito sua atitude teve na equipe ou na entrega?'
            evidence='Exemplo real, comportamento observável e consequência.'
        elif cat=='hard':
            focus='Aplicação técnica';question=f'Em que trabalho você utilizou {subject}? Descreva como aplicou esse conhecimento, quais controles usou e como verificou o resultado.'
            evidence='Aplicação prática, método, autonomia e validação.'
        else:
            focus='Condição de trabalho';question=f'A condição de trabalho informada é {subject}. Você consegue atendê-la? Explique sua disponibilidade e qualquer restrição relevante.'
            evidence='Disponibilidade objetiva e eventuais restrições.'
    # Ferramentas concretas da vaga exigem perguntas específicas, mesmo
    # quando duas ferramentas pertencem à mesma família técnica.
    if cat=='hard':
        technology_prompts=[
         (r'\bsql\b','Modelagem e consulta SQL','Conte sobre uma consulta SQL que construiu. Como relacionou tabelas, tratou filtros ou agregações e validou os resultados?','Consulta, lógica, checagens e aplicação.'),
         (r'\bpython\b','Aplicação prática de Python','Descreva uma rotina que implementou em Python. Que problema resolveu, como estruturou o código, quais testes fez e qual resultado obteve?','Código, biblioteca ou abordagem efetivamente utilizada, testes e entrega.'),
         (r'\bpower ?bi\b','Painéis no Power BI','Explique um painel que criou no Power BI. Como tratou os dados, modelou as medidas e comprovou que os indicadores estavam corretos?','Fontes, modelagem, medidas e validação.'),
         (r'\bexcel\b','Excel aplicado','Descreva uma planilha em Excel que construiu para resolver um problema. Quais fórmulas ou recursos utilizou e como conferiu os dados?','Recursos efetivamente usados, conferência e resultado.'),
         (r'wordpress','WordPress aplicado','Descreva uma página ou ajuste que realizou no WordPress. O que modificou, como publicou e verificou que funcionava corretamente?','Configuração, autonomia e validação.'),
         (r'\bcanva\b','Canva aplicado','Descreva uma peça que criou usando o Canva. Como interpretou o briefing, definiu o formato e verificou se a entrega atendeu ao objetivo?','Briefing, execução e validação.'),
         (r'\brevit\b','Revit aplicado','Conte como utilizou o Revit em um projeto. Que entregáveis produziu, quais verificações realizou e que problema técnico resolveu?','Modelo, entregas e responsabilidade técnica.'),
         (r'\bautocad\b','AutoCAD aplicado','Conte como utilizou o AutoCAD no desenvolvimento ou revisão de desenhos. Que tipo de detalhamento produziu e como verificou sua consistência?','Desenho, precisão, verificação e escopo.'),
        ]
        for regex,skill,technical_q,details in technology_prompts:
            if re.search(regex,norm(origin),re.I):
                focus=skill;question=technical_q;evidence=details;break
    # Quando responsabilidade e hard skill exigem o mesmo tema, avalia-se método
    # na pergunta técnica, não se replica a pergunta da responsabilidade.
    if cat=='hard' and detected and focus in ('Prospecção ativa','Gestão do funil e CRM','Conciliação e fechamento de valores','Implementação e dados','Gestão de mídia paga','Venda consultiva','Orçamentos e custos','Gestão de metas e indicadores'):
        technical_prompts={
         'Prospecção ativa':'Quais critérios usa para segmentar contatos e planejar uma cadência de prospecção? Descreva ferramentas, indicadores acompanhados e um ajuste que fez a partir dos dados.',
         'Gestão do funil e CRM':'Que informações e critérios você considera indispensáveis ao manter um funil no CRM? Descreva como confere a qualidade dos registros e identifica oportunidades paradas.',
         'Conciliação e fechamento de valores':'Descreva tecnicamente como estrutura uma conciliação: quais relatórios compara, como localiza diferenças e que conferências faz antes de liberar o fechamento?',
         'Implementação e dados':'Qual foi o problema técnico mais relevante que resolveu usando as tecnologias exigidas? Explique decisões de implementação, validações e testes realizados por você.',
         'Gestão de mídia paga':'Quais métricas e critérios utiliza para ajustar uma campanha nas plataformas exigidas na vaga? Dê um exemplo de decisão e dos dados que a sustentaram.',
         'Venda consultiva':'Quais técnicas ou perguntas utiliza para fazer diagnóstico de necessidades em uma venda consultiva? Dê um exemplo de como a informação obtida alterou sua proposta.',
         'Orçamentos e custos':'Quais controles e fontes de informação utiliza ao compor um orçamento? Demonstre como valida quantitativos, preços e eventuais desvios.',
         'Gestão de metas e indicadores':'Quais indicadores acompanhava na rotina da vaga e com que frequência? Como conferia os dados e identificava o que precisava de correção?'
        }
        question=technical_prompts[focus]
        evidence='Aplicação dos métodos, ferramentas e controles ligados ao requisito.'
    common=tokens(origin)&tokens(cv)
    cv_observation=''
    if cv.strip() and cat!='logistica':
        cv_observation=('O currículo traz termos relacionados a este requisito; confirmar execução concreta.' if len(common)>=2 else 'Sem evidência textual clara no currículo; investigar sem presumir ausência de competência.')
    weight={'responsabilidade':3,'hard':3,'soft':2,'logistica':1}.get(cat,2)
    if entry.get('is_differential'):weight=1
    return {'id':f'Q{idx:02d}','category':cat,'category_label':{'responsabilidade':'Responsabilidades','hard':'Hard skills','soft':'Soft skills','logistica':'Condições da vaga'}[cat],
            'criterion':origin[:250], 'origin':origin, 'line':entry['line'],'differential':bool(entry.get('is_differential')),
            'weight':weight,'question':question,'focus':focus,'expected_evidence':evidence,'cv_observation':cv_observation}

def build_questions(jd:str,cv:str='',limit:int=15)->dict:
    entries=fragments(jd)
    buckets={c:[p for p in entries if p['category']==c] for c in ('responsabilidade','hard','soft','logistica')}
    quotas={'responsabilidade':6,'hard':6,'soft':4,'logistica':1}
    selected=[]
    for cat in quotas:
        selected.extend(buckets[cat][:quotas[cat]])
    if len(selected)<min(limit,len(entries)):
        for item in entries:
            if item not in selected:selected.append(item)
            if len(selected)>=limit:break
    selected=selected[:limit]
    result=[];seen=set();asked=set()
    for row in selected:
        q=make_question(row,cv,len(result)+1)
        # Mesmo foco só é duplicado quando se investiga de fato duas dimensões distintas.
        key=(q['category'],q['focus'])
        if key in seen and q['focus'] not in ('Aplicação técnica','Comportamento em situação real','Execução da responsabilidade'):
            continue
        if q['question'] in asked:continue
        seen.add(key);asked.add(q['question']);result.append(q)
    warnings=[]
    if not jd.strip():warnings.append('A descrição está vazia. Insira o documento completo.')
    if not result:warnings.append('Não foi possível identificar requisitos ou responsabilidades. Confira a extração e edite a descrição.')
    for cat,label in [('responsabilidade','responsabilidades'),('hard','competências técnicas'),('soft','competências comportamentais')]:
        if not any(q['category']==cat for q in result):warnings.append(f'A descrição não contém {label} suficientemente explícitas; não foram inventadas perguntas dessa categoria.')
    counts={cat:sum(q['category']==cat for q in result) for cat in buckets}
    return {'questions':result,'warnings':warnings,'counts':counts,'source_fragments':len(entries),'engine':'entrevista_por_competencia_v9_5'}

def evidence_snippet(s:str,terms:set[str])->str:
    chunks=[clean(x) for x in re.split(r'[\n.!?;]+',s or '') if clean(x)]
    rated=sorted(chunks,key=lambda x:(len(tokens(x)&terms),min(250,len(x))),reverse=True)
    return rated[0][:320] if rated else ''

def disc_summary(text:str)->dict:
    if not text.strip():return {'status':'não fornecido','observations':[],'score_use':'Não integra o índice de aderência.'}
    dims=[('D','Dominância'),('I','Influência'),('S','Estabilidade'),('C','Conformidade')]
    found=[]
    for _,label in dims:
        m=re.search(rf'\b{label}\s*(?:\([DISC]\))?\s*[:\-=]?\s*(\d{{1,3}}(?:[,.]\d+)?)\s*(?:/\s*7|%)?',text,re.I)
        if m:
            v=float(m.group(1).replace(',','.'))
            if 0<=v<=100:found.append({'dimension':label,'reported_value':v,'source':'DISC fornecido'})
    if found:
        most=max(found,key=lambda x:x['reported_value'])
        prompts={'Dominância':'Verificar decisões e posicionamento em situações concretas.','Influência':'Investigar comunicação e relação com interlocutores.','Estabilidade':'Investigar rotinas, mudanças e constância.','Conformidade':'Investigar organização e checagens.'}
        return {'status':'Dimensões numéricas extraídas; verificar escala e metodologia do laudo original.', 'observations':found,'relative_observation':'Maior valor informado: '+most['dimension']+'. Não determina adequação ao cargo.', 'behavioral_validation':[prompts[x['dimension']] for x in found], 'score_use':'Não integra o índice de aderência nem constitui critério eliminatório.'}
    return {'status':'Documento disponível; dimensões não identificadas com segurança','observations':[],'score_use':'Não integra o índice de aderência. Requer leitura do relatório.'}

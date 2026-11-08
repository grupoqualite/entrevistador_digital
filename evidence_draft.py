"""Minuta editorial de parecer a partir de evidências localizadas e relatos.

Sem modelo generativo: NÃO atribui score, não deduz desempenho, não supõe resultados
não informados. Todas as frases sobre o candidato devem ter lastro documental ou
em resposta específica. As pendências operacionais ficam fora do texto do cliente.
"""
from __future__ import annotations

import re
from difflib import SequenceMatcher
from engine import tokens

SPACE = re.compile(r'\s+')
PRIVATE = re.compile(r'(?i)\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b|(?:\+?55\s*)?\(?\d{2}\)?\s*9?\d{4}[-\s]?\d{4}')
OPERATIONAL = re.compile(
    r'(?i)\b(?:importad[oa]s?|anexad[oa]s?|upload|extraíd[oa]s?|processament[oa]|'
    r'interface|sistema|plataforma|api|ollama|whisper|modelo de linguagem|'
    r'inteligência artificial|(?:IA|LLM)\s+local)\b'
)


def clean(value:object, limit:int=430)->str:
    """Limpa artefatos de texto e evita cortar palavras; nunca cria informação."""
    text=SPACE.sub(' ',str(value or '')).strip().strip('•- ')
    text=PRIVATE.sub('[contato omitido]',text)
    if len(text)<=limit:return text
    return text[:limit].rsplit(' ',1)[0].rstrip(' ,;:.')+'…'


def criterion_label(c:dict, limit=115)->str:
    return clean(c.get('criterion') or 'a atividade',limit).strip(' .;:')


def dedup_key(text:str)->str:
    return re.sub(r'\W+', ' ', text.casefold()).strip()


def unique_responses(criteria:list[dict], limit:int=7)->tuple[list[dict],int]:
    """Retém uma manifestação por exemplo substancialmente equivalente."""
    result=[];seen=[];repeated=0
    for c in criteria:
        answer=clean(c.get('answer'),1000)
        if len(answer)<20:continue
        normalized=dedup_key(answer)
        if any(SequenceMatcher(None,normalized,old).ratio()>=.84 for old in seen):
            repeated+=1
            continue
        seen.append(normalized)
        result.append({'id':c.get('id',''),'criterion':criterion_label(c),
                       'answer':answer,'category':c.get('category_key')})
        if len(result)>=limit:break
    return result,repeated


def source_passages(criteria:list[dict], source_prefix:str, limit:int=3)->list[str]:
    out=[];seen=set()
    for c in criteria:
        for item in c.get('docs',[]):
            if not str(item.get('source','')).casefold().startswith(source_prefix.casefold()):continue
            snippet=clean(item.get('excerpt'),310)
            key=dedup_key(snippet)[:130]
            if len(snippet)<18 or key in seen or '[contato omitido]' in snippet:continue
            seen.add(key)
            out.append(snippet)
            if len(out)>=limit:return out
    return out


def source_sentences(text:str,criteria:list[dict],limit:int=2)->list[str]:
    """Usa trechos do histórico apenas quando relevantes à função, sem reinterpretá-los."""
    if not text or not criteria:return []
    terms=set()
    for c in criteria:terms|=tokens(c.get('criterion',''))
    lines=re.split(r'(?<=[.!?])\s+|[\r\n]+',str(text))
    candidates=[];seen=set()
    for index,line in enumerate(lines):
        line=clean(line,310)
        if not (35<=len(line)<=325):continue
        if '[contato omitido]' in line:continue
        key=dedup_key(line)
        if key in seen:continue
        seen.add(key)
        overlap=len(tokens(line)&terms)
        if overlap:candidates.append((overlap,min(len(line),240),-index,line))
    candidates.sort(reverse=True)
    return [x[-1] for x in candidates[:limit]]


def quote_snippet(value:str,limit:int=285)->str:
    """Citação literal curta. Marcadores de corte não se confundem com a fala original."""
    value=clean(value,limit)
    return '“'+value.strip('“”').rstrip('.!?;')+'”'


def join_topics(values:list[str],max_items:int=3)->str:
    seen=set();out=[]
    for value in values:
        item=value.strip(' .;:')
        key=dedup_key(item)
        if not item or key in seen:continue
        out.append(item[:1].lower()+item[1:] if item else item)
        seen.add(key)
        if len(out)>=max_items:break
    if not out:return ''
    if len(out)==1:return out[0]
    return ', '.join(out[:-1])+' e '+out[-1]


def _has_result(answer:str)->bool:
    """Só marca existência de dado de desempenho quando há indicação concreta."""
    return bool(re.search(
        r'(?i)(?:\b(?:atingi|aumentei|reduzi|economizei|fechei|concluí|entreguei)\b.{0,35}\d+'
        r'|\b\d+(?:[.,]\d+)?\s*(?:%|clientes|vendas|pedidos|reuniões|contratos|dias|horas|semanas|meses)\b'
        r'|R\$\s*\d+)',str(answer or '')))


def lower_start(value:str)->str:
    """Converte verbo inicial a minúscula em frase, preservando siglas."""
    if len(value)>1 and value[0].isupper() and value[1].islower():
        return value[0].lower()+value[1:]
    return value


def explicit_non_experience(answer:str)->bool:
    """Detecta negativas inequívocas; silêncio não implica ausência de competência."""
    return bool(re.search(
        r'\b(?:nunca fiz|nunca atuei|nunca trabalhei|não fiz|não exerci|não atuei|'
        r'não trabalhei|não tenho experiência|não possuo experiência|não tive experiência|'
        r'não realizei|ainda não fiz|ainda não atuei|sem experiência com)\b',
        str(answer or '').casefold()))


def thematic_requirement(criterion:str)->str:
    """Relaciona o critério ao resultado da função, sem afirmar domínio do candidato."""
    val=criterion.casefold()
    groups=[
        (('atendiment','clientes','whatsapp','telefone','recepção'),
         'qualidade do atendimento, identificação de necessidades e continuidade do contato com o cliente'),
        (('vend','negocia','prospec','funil','crm','comercial'),
         'condução das oportunidades, organização do processo comercial e resultados obtidos'),
        (('medicament','farmácia','pedido','dispensa','confer'),
         'conferência das informações, prevenção de erros e cumprimento das rotinas operacionais'),
        (('obra','cronogram','fornecedor','constru','projeto','orçament'),
         'controle de execução, acompanhamento de prazos e coordenação dos envolvidos'),
        (('financeir','concilia','contas','fatur','fluxo de caixa'),
         'precisão dos controles, conciliação dos registros e cumprimento de prazos'),
        (('marketing','tráfego','campanha','conteúdo','meta ads'),
         'planejamento das ações, acompanhamento de indicadores e ajustes executados'),
        (('desenvolv','programa','sistem','código','software','dados'),
         'aplicação técnica, qualidade da entrega e resolução de problemas'),
    ]
    for keys,explanation in groups:
        if any(key in val for key in keys):return explanation
    return 'participação efetiva na rotina, autonomia das decisões e resultados entregues'


def quote_paragraph(evidence:dict, opener:str='Na entrevista')->str:
    topic=lower_start(evidence['criterion'])
    answer=evidence['answer']
    if explicit_non_experience(answer):
        return (f'Em relação a {topic}, o candidato informou uma limitação de experiência: '
                f'{quote_snippet(answer,290)}. A declaração delimita a vivência relatada nessa '
                'responsabilidade específica, sem invalidar automaticamente experiências próximas '
                'que possam ser aproveitadas após treinamento.')
    val=topic.casefold()
    story=answer.casefold()
    # As implicações abaixo se referem apenas ao exemplo descrito, sem inferir competência estável.
    if ('atend' in val or 'cliente' in val) and ('estoque' in story or 'produto' in story):
        insight=('A resposta descreve etapas de atendimento, consulta de disponibilidade ou '
                 'encaminhamento de demanda, atividades diretamente relacionadas ao contato com clientes.')
    elif ('confer' in val or 'pedido' in val) and ('quantidad' in story or 'diverg' in story):
        insight=('O exemplo trata de conferência das informações e tratamento de divergências, '
                 'aspectos relevantes para reduzir erros operacionais.')
    elif ('metas' in val or 'vendas' in val) and ('atendiment' in story or 'pedido' in story):
        insight=('A resposta diferencia o acompanhamento da própria rotina da responsabilidade '
                 'pelas metas e resultados globais, distinção relevante para dimensionar autonomia.')
    else:
        insight=f'O exemplo se relaciona a {thematic_requirement(topic)}, embora a extensão da atuação deva ser verificada.'
    if _has_result(answer):
        final=('Os indicadores ou resultados mencionados permanecem declaratórios e precisam '
               'ser contextualizados conforme as responsabilidades assumidas.')
    else:
        final=('Não há, nesse relato específico, elementos objetivos suficientes para aferir '
               'volume de entregas ou desempenho quantitativo.')
    return (f'{opener}, ao tratar de {topic}, o candidato relatou: {quote_snippet(answer,320)}. '
            f'{insight} {final}')

def doc_paragraph(passages:list[str],role:str, source:str)->str:
    if source=='cv':
        lead='A trajetória profissional apresentada registra experiências relacionadas à função'
    else:
        lead='O histórico profissional também traz referências a atividades relacionadas à vaga'
    segments='; '.join(quote_snippet(x,260) for x in passages[:2])
    return (f'{lead} de {role}: {segments}. '
            'Essas referências contribuem para identificar campos de atuação, embora, isoladamente, '
            'não determinem a autonomia, a frequência das entregas ou o desempenho alcançado.')


def identify_gaps(technical:list[dict],behavior:list[dict],tech_answers:list[dict],soft_answers:list[dict],
                  cv:bool,linkedin:bool,disc:bool)->tuple[list[str],list[str]]:
    def count_matches(questions,answers):
        answered={x['id'] for x in answers}
        return [criterion_label(c) for c in questions if c.get('id') not in answered]
    tech_gaps=[];soft_gaps=[]
    unaddressed=count_matches(technical,tech_answers)
    if unaddressed:
        tech_gaps.append('Aprofundar a aplicação prática de '+join_topics(unaddressed,3)+'.')
    if tech_answers and not any(_has_result(e['answer']) for e in tech_answers):
        tech_gaps.append('Confirmar resultados, indicadores de desempenho e participação direta nas entregas relatadas.')
    if not cv and not linkedin:
        tech_gaps.append('Reconstruir o histórico profissional, as funções exercidas e os períodos de experiência.')
    for item in tech_answers:
        if explicit_non_experience(item['answer']):
            tech_gaps.insert(0,'Confirmar a necessidade de treinamento para '+item['criterion'].lower()+'.')
    if not tech_answers:
        tech_gaps.append('Aprofundar a prática efetiva das atividades essenciais, esclarecendo método, autonomia e resultados.')
    soft_missing=count_matches(behavior,soft_answers)
    if soft_missing:
        soft_gaps.append('Solicitar um exemplo observável de '+join_topics(soft_missing,2)+'.')
    if not soft_answers:
        soft_gaps.append('Explorar situações reais de interação, decisão, pressão e resolução de problemas.')
    if disc and not soft_answers:
        soft_gaps.append('Confrontar o perfil comportamental informado com situações reais da experiência profissional.')
    return tech_gaps[:4],soft_gaps[:3]



# A versão cliente sintetiza a experiência profissional, não o processo de coleta.
# O conteúdo completo das fontes continua disponível internamente para auditoria.
from behavioral_analysis import build_behavioral, split_document, negated

CAREER_AREAS = [
  (r'atendiment|recep[cç][aã]o|balc[aã]o','atendimento e relacionamento com clientes'),
  (r'vendas?|comercial|prospec|negocia','rotinas comerciais'),
  (r'pedido|estoque|separa[cç][aã]o|log[ií]stica','controle de pedidos e estoque'),
  (r'confer[eê]ncia|qualidade|inspe[cç][aã]o|checagem','conferência e controle de qualidade'),
  (r'crm|funil|follow.up|indicador|sla','registro e acompanhamento de indicadores e processos'),
  (r'obra|cronograma|or[cç]amento|execu[cç][aã]o','acompanhamento de projetos e entregas'),
  (r'financeir|fatur|concilia|contas a pagar|fluxo de caixa','rotinas financeiras e controles'),
  (r'campanha|marketing|m[ií]dia paga|social media|tr[aá]fego','ações de marketing e comunicação'),
  (r'desenvolvimento de software|python|programa[cç][aã]o|sql|dados','desenvolvimento ou análise de sistemas e dados'),
]

TECH_ACTIONS = [
  (r'\b(?:atendia|atendi|atendimento de balc[aã]o|atendimento presencial|atendimento ao p[uú]blico)\b','atendimento ao público'),
  (r'\bwhatsapp\b','contato por WhatsApp'),
  (r'\b(?:esclareci|orientei|expliquei)\b','orientação ao cliente'),
  (r'\b(?:conferia|conferi|chequei|verificava|verifiquei|comparava|comparei)\b','conferência de informações'),
  (r'\b(?:pedido|pedidos)\b','rotina de pedidos'),
  (r'\b(?:crm|erp)\b','uso de sistema de gestão'),
  (r'\b(?:estoque|invent[aá]rio)\b','consulta ou acompanhamento de estoque'),
  (r'\b(?:funil|prospec[cç][aã]o|leads?)\b','processo de prospecção e acompanhamento comercial'),
  (r'\b(?:indicador|metas?|convers[aã]o)\b','acompanhamento de resultados'),
  (r'\b(?:or[cç]amento|cronograma|fornecedores?)\b','controle de etapas e recursos'),
  (r'\b(?:excel|planilha|relat[oó]rio)\b','registro ou análise de informações'),
]


def _facts(text:str,areas=TECH_ACTIONS,max_items=5)->list[str]:
    seen=set();out=[]
    for pattern,label in areas:
        if re.search(pattern,str(text or ''),re.I) and label not in seen:
            out.append(label);seen.add(label)
        if len(out)>=max_items:break
    return out


def _doc_areas(cv:str,linkedin:str)->list[str]:
    # Seleciona menções positivas em frases da trajetória, evitando confundir
    # 'não tenho experiência em X' com evidência favorável de X.
    source=split_document(cv)+split_document(linkedin)
    # Documentos curtos podem não conter frases longas; ainda assim excluímos
    # negativas explícitas e duplicatas.
    if not source:
        source=[x.strip() for x in re.split(r'[\n.]+',(cv or '')+'\n'+(linkedin or '')) if len(x.strip())>18]
    affirmative=' '.join(x for x in source if not negated(x))
    terms=[]
    for pattern,label in CAREER_AREAS:
        if re.search(pattern,affirmative,re.I):terms.append(label)
    return terms[:5]


def _technical_account(e:dict)->str:
    topic=lower_start(e['criterion']).strip(' .')
    answer=e['answer']
    if explicit_non_experience(answer):
        scope=''
        if re.search(r'produtos? de higiene',answer,re.I):
            scope=' A experiência informada limita-se, nesse aspecto, a produtos de higiene.'
        return (f'Não há experiência direta declarada em {topic}.{scope} '
                'Essa diferença precisa ser considerada à luz da exigência operacional da função e das possibilidades de treinamento, '
                'sem desconsiderar experiências próximas de atendimento ou conferência.')
    facts=_facts(answer)
    if len(facts)>=2:
        text=(f'Na atuação relacionada a {topic}, descreve {_natural_join(facts[:4])}. '
              'As atividades são pertinentes ao escopo da posição, mas a extensão da responsabilidade pessoal '
              'e o grau de autonomia dependem do contexto em que foram executadas.')
    elif facts:
        text=(f'Para {topic}, há referência prática a {facts[0]}. '
              'O elemento aproxima a experiência da atividade requerida, mas não esclarece, isoladamente, '
              'frequência, método de execução ou participação nas decisões.')
    else:
        text=(f'O histórico ainda não oferece descrição operacional suficiente para aferir a experiência em {topic}. '
              'Não é adequado presumir domínio técnico apenas pela familiaridade com o nome da atividade.')
    if _has_result(answer):
        text+=' Há menção a resultados ou indicadores, ainda dependentes de contextualização sobre período, base de comparação e participação pessoal.'
    return text


def _natural_join(items):
    items=[str(x) for x in items if x]
    if not items:return ''
    if len(items)==1:return items[0]
    return ', '.join(items[:-1])+' e '+items[-1]


def draft_from_sources(report:dict,cv_text:str='',linkedin_text:str='',disc_text:str='')->dict:
    """Redige minuta profissional com análise interdisciplinar e pontos de validação.

    Sem motor semântico, esta análise é conservadora: regras localizam condutas
    descritas e não emitem julgamento de personalidade, score ou recomendação.
    O recrutador mantém poder de revisar, ratificar e definir recomendação.
    """
    criteria=report.get('criteria') or []
    responsibilities=[c for c in criteria if c.get('category_key')=='responsabilidade']
    hard=[c for c in criteria if c.get('category_key')=='hard']
    tech=responsibilities+hard
    behavior=[c for c in criteria if c.get('category_key')=='soft']
    cv=bool(str(cv_text or '').strip());li=bool(str(linkedin_text or '').strip())
    if not (cv or li or any(str(c.get('answer','')).strip() for c in criteria)):
        raise ValueError('Ainda não há evidências profissionais suficientes para redigir uma minuta. Confira os registros da candidatura.')
    role=clean(report.get('job_title') or 'a oportunidade',120)
    t_answers,repeated=unique_responses(tech,10)
    soft_answers,_=unique_responses(behavior,10)
    gaps_tech,gaps_soft=identify_gaps(tech,behavior,t_answers,soft_answers,cv,li,bool(disc_text))
    technical=[]
    career_areas=_doc_areas(cv_text,linkedin_text)
    if career_areas:
        technical.append(
            f'A trajetória profissional reúne experiências relacionadas a {_natural_join(career_areas[:4])}. '
            f'Para a posição de {role}, esse repertório deve ser considerado conforme a proximidade com as atribuições centrais, '
            'distinguindo experiências diretamente executadas de atividades de suporte. '
            'A presença dessas atividades no histórico não permite presumir volume, resultados ou autonomia que não tenham sido descritos.'
        )
    elif cv or li:
        technical.append(
            f'A trajetória profissional exige maior detalhamento para estabelecer a correspondência com as atribuições de {role}. '
            'Antes de concluir o nível de domínio técnico, é necessário delimitar as atividades efetivamente exercidas, '
            'a responsabilidade pelas entregas e a experiência no contexto específico da função.'
        )
    tasks=[criterion_label(c) for c in responsibilities[:4]]
    if tasks:
        technical.append(
            f'Entre as responsabilidades da função estão {_natural_join([lower_start(x) for x in tasks[:3]])}. '
            'A análise dessas atividades exige verificar a prática no ambiente real, a segurança dos procedimentos, '
            'o acompanhamento das entregas e a capacidade de lidar com situações fora da rotina.'
        )
    described=[e for e in t_answers if e['category']=='responsabilidade'][:5]
    described += [e for e in t_answers if e['category']=='hard'][:3]
    positive=[e for e in described if not explicit_non_experience(e['answer'])]
    denied=[e for e in described if explicit_non_experience(e['answer'])]
    if positive:
        action_labels=[]
        for entry in positive:
            for fact in _facts(entry['answer']):
                if fact not in action_labels:action_labels.append(fact)
        if action_labels:
            technical.append(
                'Na rotina profissional, descreve atividades como '+_natural_join(action_labels[:6])+'. '
                'Esses elementos oferecem base para reconhecer familiaridade com etapas da operação, '
                'mas devem ser dimensionados conforme a responsabilidade direta, o método aplicado '
                'e a frequência das entregas. Não se pode equiparar o uso pontual de uma ferramenta '
                'ao domínio integral do processo em que ela é utilizada.'
            )
        else:
            technical.append(
                'A experiência descrita ainda não detalha os procedimentos utilizados nas atividades centrais '
                'da função. É necessário identificar o que foi executado diretamente, quais recursos foram usados '
                'e como a qualidade da entrega foi conferida.'
            )
        for e in positive:
            if e['category']=='hard' and len(_facts(e['answer']))>=1:
                technical.append(
                    f'No âmbito de {lower_start(e["criterion"]).strip(" .")}, a experiência informada inclui '
                    f'{_natural_join(_facts(e["answer"])[:3])}. O contexto relatado permite avaliar familiaridade '
                    'com a rotina, mas não comprova resultados quantitativos nem responsabilidade integral pelas metas '
                    'sem informações complementares.'
                )
                break
    else:
        technical.append(
            'Não foram descritos episódios suficientemente específicos para dimensionar a execução das '
            'responsabilidades essenciais. A ausência de detalhamento não permite concluir que as competências '
            'inexistam, mas exige validação direta antes de recomendar o candidato.'
        )
    if denied:
        denied_labels=[lower_start(e['criterion']) for e in denied]
        contextual=[]
        if any(re.search(r'produtos? de higiene',e['answer'],re.I) for e in denied):
            contextual.append('a atuação mencionada ficou restrita a produtos de higiene')
        technical.append(
            'Há uma lacuna expressamente indicada quanto a '+_natural_join(denied_labels[:2])+'. '
            +('Nesse aspecto, '+_natural_join(contextual)+'. ' if contextual else '')
            +'A diferença deve ser avaliada de acordo com a necessidade de experiência prévia e com os procedimentos de treinamento da organização.'
        )
    if repeated:
        gaps_tech.append('Aprofundar outras experiências profissionais, além do mesmo episódio usado para diferentes critérios.')

    behavioral,pending_beh,behavior_trace=build_behavioral(criteria,cv_text,linkedin_text,disc_text,report.get('disc'))
    # Registra o mapa de fontes somente no relatório interno; não será incluído no PDF de cliente.
    if not behavioral:
        behavioral=['Não há condutas observáveis suficientes para caracterizar com segurança as competências comportamentais exigidas.']
    gaps_soft = list(dict.fromkeys(pending_beh+gaps_soft))[:4]
    positive=[x for x in career_areas[:3]]
    rec=[]
    if positive:
        rec.append(
            f'Para a vaga de {role}, o histórico indica exposição profissional a {_natural_join(positive)}. '
            'A proximidade com as exigências da posição depende de comprovar a prática direta nas atividades essenciais, '
            'o alcance das responsabilidades e os resultados efetivamente obtidos.'
        )
    elif described:
        rec.append(
            f'Para a vaga de {role}, foram identificados elementos de experiência relacionados a parte das atividades previstas. '
            'O grau de aderência permanece condicionado à consistência das experiências e à validação das atribuições efetivamente executadas.'
        )
    else:
        rec.append(
            f'Para a vaga de {role}, os elementos disponíveis ainda não permitem uma conclusão segura sobre aderência técnica e comportamental. '
            'Essa insuficiência de evidências não equivale, por si só, a inadequação profissional.'
        )
    if denied:
        rec.append('É necessário considerar a ausência de experiência direta declarada em '+_natural_join([lower_start(x['criterion']) for x in denied[:2]])+'.')
    next_points=[]
    for point in gaps_tech+gaps_soft:
        if point and point.casefold() not in [x.casefold() for x in next_points]:next_points.append(point.strip().rstrip('.'))
        if len(next_points)>=3:break
    if next_points:
        rec.append('Antes de uma indicação conclusiva, convém '+ '; '.join(x[0].lower()+x[1:] for x in next_points)+'.')
    rec.append('A decisão de recomendar o avanço deverá ser registrada pelo recrutador, após a avaliação das evidências e das condições efetivas da oportunidade.')
    return {
      'tecnicas':technical[:7],
      'comportamentais':behavioral[:6],
      'validacoes_tecnicas':list(dict.fromkeys(gaps_tech))[:4],
      'validacoes_comportamentais':gaps_soft,
      'recomendacao':'\n\n'.join(rec),
      'evidencias_comportamentais_internas':behavior_trace,
      'modo':'Minuta documental com cruzamento de informações profissionais e avaliação humana obrigatória',
      'aviso':'Conferência do recrutador obrigatória antes da aprovação.'
    }

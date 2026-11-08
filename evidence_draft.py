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
        tech_gaps.append('As respostas estão ausentes ou curtas demais para demonstrar execução prática; solicitar casos que esclareçam método, autonomia e resultados.')
    soft_missing=count_matches(behavior,soft_answers)
    if soft_missing:
        soft_gaps.append('Solicitar um exemplo observável de '+join_topics(soft_missing,2)+'.')
    if not soft_answers:
        soft_gaps.append('Explorar situações reais de interação, decisão, pressão e resolução de problemas.')
    if disc and not soft_answers:
        soft_gaps.append('Confrontar o perfil comportamental informado com situações reais da experiência profissional.')
    return tech_gaps[:4],soft_gaps[:3]


def draft_from_sources(report:dict, cv_text:str='', linkedin_text:str='', disc_text:str='')->dict:
    """Minuta aprofundada. A análise qualitativa requer leitura e aprovação humana.

    Não atribui notas, não afirma competência apenas por correspondência de palavras
    e não produz recomendação positiva/negativa automaticamente.
    """
    criteria=report.get('criteria') or []
    responsibilities=[c for c in criteria if c.get('category_key')=='responsabilidade']
    hard=[c for c in criteria if c.get('category_key')=='hard']
    tech=responsibilities+hard
    behavior=[c for c in criteria if c.get('category_key')=='soft']
    cv=bool(str(cv_text).strip());li=bool(str(linkedin_text).strip());disc=bool(str(disc_text).strip())
    if not (cv or li or any(str(c.get('answer','')).strip() for c in criteria)):
        raise ValueError('Sem respostas nem histórico profissional para fundamentar o parecer. Confira os registros antes de gerar a minuta.')
    role=clean(report.get('job_title') or 'a oportunidade',100)
    t_answers,trepeat=unique_responses(tech,7)
    b_answers,brepeat=unique_responses(behavior,4)
    doc_cv=source_passages(tech,'Curr',3) or source_sentences(cv_text,tech,2)
    doc_li=source_passages(tech,'LinkedIn',2) or source_sentences(linkedin_text,tech,2)
    t_pending,b_pending=identify_gaps(tech,behavior,t_answers,b_answers,cv,li,disc)
    technical=[];behavioral=[]

    if doc_cv or doc_li:
        prior={dedup_key(x) for x in doc_cv}
        unique=[x for x in doc_li if dedup_key(x) not in prior]
        sources=(doc_cv[:2]+unique[:1])
        technical.append(
            f'Na trajetória profissional, há experiências relacionadas ao escopo de {role}, '
            'com registros como '+ '; '.join(quote_snippet(x,250) for x in sources)+'. '
            'Esse histórico indica contato com parte das rotinas pertinentes à função. A extensão '
            'das responsabilidades e os resultados alcançados precisam ser dimensionados pelos '
            'exemplos concretos da entrevista, especialmente quando a atividade exige prática específica.'
        )
    if not (doc_cv or doc_li) and (cv or li):
        technical.append(
            'O histórico profissional apresentado ainda não permite relacionar com precisão as experiências '
            f'às principais atribuições de {role}. A profundidade da atuação, os períodos e a responsabilidade '
            'pelas entregas devem ser esclarecidos antes de uma conclusão sobre domínio técnico.'
        )

    related=[criterion_label(c) for c in responsibilities[:3]]
    if related and t_answers:
        technical.append(
            f'Considerando o escopo de {role}, as responsabilidades centrais envolvem {join_topics(related)}. '
            'A entrevista permite examinar como o candidato participou dessas rotinas, '
            'distinguindo a execução direta de atividades de apoio e da responsabilidade por resultados.'
        )
    res_answers=[e for e in t_answers if e['category']=='responsabilidade']
    hard_answers=[e for e in t_answers if e['category']=='hard']
    for e in res_answers[:3]:technical.append(quote_paragraph(e))
    if hard_answers:
        e=hard_answers[0]
        technical.append(quote_paragraph(e,'Quanto aos conhecimentos e recursos necessários à função'))
        if len(hard_answers)>1:
            other=hard_answers[1]
            technical.append(
                f'Ainda no campo técnico, ao abordar {lower_start(other["criterion"])}, descreveu: '
                f'{quote_snippet(other["answer"],300)}. '
                'A análise precisa distinguir familiaridade com essa atividade de aplicação autônoma '
                'e recorrente na rotina profissional.'
            )
    if not t_answers:
        technical.append(
            'As informações profissionais disponíveis não foram acompanhadas de exemplos suficientemente '
            'específicos de execução das atividades previstas na vaga. Por isso, não há base para afirmar '
            'domínio prático, resultados alcançados ou autonomia sobre as principais entregas.'
        )
    if trepeat:
        technical.append(
            'Parte das respostas apresentou o mesmo exemplo para diferentes requisitos. '
            'Esse relato foi considerado uma única evidência, não demonstrações independentes '
            'de competências distintas. É importante aprofundar as atividades ainda não exemplificadas.'
        )


    if b_answers:
        behavioral.append(
            'A entrevista traz situações concretas que permitem avaliar a conduta profissional descrita, '
            'principalmente na relação com clientes, organização da rotina e encaminhamento de problemas. '
            'A consistência desses comportamentos deve ser considerada à luz de outros episódios e da experiência acumulada.'
        )
        for e in b_answers[:3]:
            theme=e['criterion'].casefold()
            if 'comunic' in theme or 'relacion' in theme:
                comment=('O episódio traz uma situação de interação com outra pessoa e permite avaliar '
                         'como o candidato descreve a escuta, a comunicação e o encaminhamento da demanda.')
            elif 'organiza' in theme or 'atenção' in theme or 'detalh' in theme:
                comment=('O relato descreve procedimentos de organização e conferência, úteis para '
                         'examinar o cuidado com a execução e a prevenção de falhas na rotina.')
            elif 'autonom' in theme or 'decis' in theme or 'iniciativ' in theme:
                comment=('A experiência relatada oferece elementos para examinar participação pessoal '
                         'na decisão e as alternativas consideradas diante do problema.')
            else:
                comment=('O relato fornece um episódio profissional específico, cuja consistência '
                         'deve ser confrontada com outros exemplos de atuação.')
            behavioral.append(
                f'Em relação a {lower_start(e["criterion"])}, o candidato relatou: {quote_snippet(e["answer"],330)}. '
                +comment
            )
    else:
        behavioral.append(
            'As declarações disponíveis não trazem situações suficientemente detalhadas para caracterizar '
            'com segurança os comportamentos requeridos pela função. A avaliação deve explorar casos '
            'concretos de relacionamento, organização e tomada de decisão pertinentes às exigências da vaga.'
        )
    if brepeat:
        behavioral.append(
            'O mesmo episódio foi utilizado em respostas a diferentes competências comportamentais. '
            'Ele foi tratado como um relato único; convém solicitar outro exemplo antes de atribuir '
            'a mesma interpretação a características distintas.'
        )
    observations=(report.get('disc') or {}).get('observations') or []
    if disc and observations:
        values=[]
        for o in observations[:6]:
            dimension=clean(o.get('dimension'),70);value=clean(o.get('reported_value') or 'não informado',50)
            if dimension:values.append(f'{dimension}: {value}')
        if values:
            behavioral.append(
                'No DISC, os indicadores apresentados são '+', '.join(values)+'. '
                'A leitura dessas dimensões deve observar a escala e a interpretação do instrumento aplicado. '
                'O perfil contribui como referência complementar, sem substituir os comportamentos '
                'demonstrados na entrevista nem permitir previsões isoladas de desempenho.'
            )
    elif disc:
        # Não menciona upload, extração ou falhas de processamento em documento do cliente.
        b_pending.append('Conferir a leitura integral do DISC e sua correspondência com situações profissionais concretas.')
    if b_pending:
        behavioral.append(
            'Para complementar a análise comportamental, recomenda-se '+
            '; '.join(x[:1].lower()+x[1:].rstrip('.') for x in b_pending[:2])+'.'
        )

    covered=[e['criterion'] for e in t_answers if not explicit_non_experience(e['answer'])]
    denied=[e['criterion'] for e in t_answers if explicit_non_experience(e['answer'])]
    doc_supported=bool(doc_cv or doc_li)
    if covered:
        opening=(f'Para a posição de {role}, a entrevista contém relatos relacionados a '
                 f'{join_topics(covered,3)}. ')
        strength=('O histórico profissional oferece informações adicionais sobre áreas de atuação, '
                  'sem comprovar, por si só, a extensão dos resultados.' if doc_supported else
                  'A consistência desses relatos deverá ser verificada em conjunto com o histórico de experiência.')
    elif doc_supported:
        opening=(f'Para a posição de {role}, o histórico profissional apresenta experiências associadas '
                 'a parte das atividades requeridas. ')
        strength='Ainda faltam exemplos de execução e resultados que permitam dimensionar a aderência prática.'
    else:
        opening=f'Para a posição de {role}, não há evidências suficientemente específicas para uma conclusão de aderência técnica. '
        strength='A ausência desses elementos não equivale à ausência de experiência, mas impede uma recomendação fundamentada neste momento.'
    gaps=[x for x in (t_pending+b_pending) if not (denied and 'treinamento' in x.casefold() and any(y.casefold() in x.casefold() for y in denied))][:4]
    rec=[opening+strength]
    if denied:
        rec.append('O candidato declarou não ter experiência direta em '+join_topics(denied,2)+'. '
                   'Essa diferença em relação ao escopo da posição merece verificação sobre o nível de prática requerido e a possibilidade de treinamento.')
    if gaps:
        rec.append('Na próxima etapa, os pontos prioritários de validação são '+
                   '; '.join(x[:1].lower()+x[1:].rstrip('.') for x in gaps)+'. '
                   'A confirmação deve se apoiar em situações reais, atribuições efetivas e resultados informados.')
    rec.append(
        'A recomendação de encaminhamento deve ser definida pelo recrutador após conferir '
        'a consistência das evidências e as condições específicas da oportunidade. '
        'Os elementos ainda não demonstrados foram mantidos como pendências, sem presunção de inadequação.'
    )

    return {'tecnicas':technical[:9], 'comportamentais':behavioral[:7],
            'validacoes_tecnicas':t_pending,'validacoes_comportamentais':b_pending,
            'recomendacao':'\n\n'.join(rec),
            'modo':'minuta profissional baseada em evidências, sem pontuação automática',
            'aviso':'Conferência editorial e técnica obrigatória pelo recrutador antes de aprovar o parecer.'}

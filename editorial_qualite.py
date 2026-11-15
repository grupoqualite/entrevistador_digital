"""Parecer Qualité: síntese ANALÍTICA, sem transcrição literal no PDF do cliente.

As evidências originais permanecem apenas no processo interno. A função não
atribui notas, não presume resultados e não substitui a revisão do recrutador.
"""
from __future__ import annotations
import re
import unicodedata

ACTION_MAP = (
    (r'\b(?:atendi|atendia|atendimento|atender|p[uú]blico|clientes?)\b', 'atendimento e relacionamento com o público'),
    (r'\bwhatsapp\b', 'atendimento por WhatsApp'),
    (r'\b(?:escut|ouvi|ouvindo|necessidad|identificava o que|entender o cliente)', 'levantamento das necessidades do cliente'),
    (r'\b(?:indica|orienta|explic|esclarec|informa|suger)', 'orientação e esclarecimento de dúvidas'),
    (r'\b(?:pedidos?|encomendas?)\b', 'recebimento ou acompanhamento de pedidos'),
    (r'\b(?:entrega|motoboy|despacho|expedi[cç][aã]o)\b', 'acompanhamento de entregas'),
    (r'\b(?:prazo|agenda|prioridade|ordem de vez|por ordem)\b', 'organização de prazos e prioridades'),
    (r'\b(?:metas?|resultados?|indicadores?|convers[aã]o)\b', 'vivência com metas ou indicadores'),
    (r'\b(?:propostas?|or[cç]amentos?)\b', 'elaboração ou acompanhamento de propostas'),
    (r'\b(?:vendas?|vendi|negocia|fechamento|comercial)\b', 'rotinas comerciais'),
    (r'\b(?:crm|funil|leads?|prospec[cç][aã]o)\b', 'prospecção ou acompanhamento comercial'),
    (r'\b(?:confer[iê]|conferencia|checagem|verifiquei\s+(?:pedido|dados|medicamento))\w*', 'conferência de informações'),
    (r'\b(?:estoque|invent[aá]rio)\b', 'acompanhamento de estoque'),
    (r'\b(?:caixa|pagamento|recebimento)\b', 'operações de caixa ou recebimento'),
    (r'\b(?:planilha|excel|relat[oó]rio)\b', 'registros ou controles em planilhas'),
    (r'\b(?:trein|capacita|lider|coordena|supervis)\w*', 'orientação ou coordenação de equipes'),
)
GENERIC = re.compile(r'(?i)novo crit[eé]rio|inserir origem|pergunta inserida|q\d{2}\b|(?:https?://|www\.)')
PRIVATE = re.compile(r'(?i)\b(?:casad[oa]|solteir[oa]|filhos?|idade|religião|gravidez|diagn[oó]stico)\b')
DENIAL = re.compile(r'(?i)\b(?:n[aã]o (?:tenho|possuo|atuei|trabalhei|fiz|realizei|sei)|nunca (?:atuei|fiz|trabalhei)|sem experi[eê]ncia)\b')


def _normalize(v):
    return ''.join(c for c in unicodedata.normalize('NFKD',str(v or '').casefold()) if not unicodedata.combining(c))


def _clean(v, limit=180):
    s=re.sub(r'\s+',' ',str(v or '')).strip(' \n.,;:•')
    return s if len(s)<=limit else s[:limit].rsplit(' ',1)[0].rstrip(' .,;:')


def _join(items):
    items=[str(x) for x in items if x]
    if not items:return ''
    if len(items)==1:return items[0]
    return ', '.join(items[:-1])+' e '+items[-1]


def _activities(text, limit=7):
    # Não equivale a constatar domínio: apenas identifica temas nas declarações.
    value=_normalize(text)
    found=[]
    for regex,label in ACTION_MAP:
        if re.search(regex,value,re.I) and label not in found:found.append(label)
    return found[:limit]


def _criteria(report,category):
    return [c for c in report.get('criteria',[]) if c.get('category_key') in category
            and not GENERIC.search(c.get('criterion',''))]


def _answers(cs):
    return [str(c.get('answer') or '').strip() for c in cs if c.get('answer')]


def _career(cv,linkedin,narrative):
    src=_normalize('\n'.join((cv,linkedin,narrative)))
    areas=[]
    mapping=(
        (r'inspetor de alunos|professores|alunos','atendimento e orientação em ambiente educacional'),
        (r'farm[aá]cia|distribuidora de medicamentos|medicamentos','atividades vinculadas ao segmento farmacêutico ou distribuição de medicamentos'),
        (r'operador de caixa|caixa','operações de caixa'),
        (r'atendiment|p[uú]blico|clientes','contato direto com o público'),
        (r'vend|comercial|prospec|negoci','área comercial e relacionamento com clientes'),
        (r'log[ií]stica|estoque|pedidos|entrega','apoio a pedidos ou operações logísticas'),
        (r'gest[aã]o|coordena|lider|supervis','atividades de liderança ou coordenação'),
        (r'marketing|campanha|m[ií]dia','comunicação ou marketing'),
        (r'obra|engenharia|projeto','projetos e operações técnicas'),
        (r'financeir|cont[aá]bil|faturamento','rotinas financeiras'),
    )
    for rg,label in mapping:
        if re.search(rg,src) and label not in areas:areas.append(label)
    # Identifica nomes de organizações sem confundir esses dados com competências.
    employers=[]
    for m in re.finditer(r'\b(?:na|no|pela|pelo)\s+([A-ZÁÀÂÉÊÍÓÔÚÇ][\wÀ-ÿ]+(?:\s+[A-ZÁÀÂÉÊÍÓÔÚÇ][\wÀ-ÿ]+){0,3})\b',cv or ''):
        comp=_clean(m.group(1),65)
        if comp not in employers and not PRIVATE.search(comp) and comp.casefold() not in ('empresa','área','atividade'):
            employers.append(comp)
    return areas[:5],employers[:2]


def _operational_findings(answers):
    """Mapeia relações tarefa -> método -> resultado, nunca citações literais.

    Um padrão precisa estar presente na mesma resposta, evitando criar um
    episódio composto por afirmações que ocorreram em contextos diferentes.
    """
    items=[]
    for answer in answers:
        txt=_normalize(answer)
        if re.search(r'prospect|leads?',txt) and re.search(r'telefon|whatsapp',txt) and re.search(r'decisor|reunia|agenda',txt):
            items.append('Na prospecção, a sequência descrita vai do contato por telefone ou WhatsApp à identificação do interlocutor responsável e ao agendamento de reuniões. Isso demonstra compreensão de etapas de qualificação comercial; o desempenho deve ser confirmado por indicadores de conversão e resultados.')
        if re.search(r'crm',txt) and re.search(r'registr|atualiz|funil',txt) and re.search(r'propost|negocia|lead',txt):
            items.append('O uso de CRM foi associado ao registro de oportunidades, à atualização do funil e ao acompanhamento de propostas ou negociações. Há correspondência com o controle de um pipeline comercial, embora a complexidade da carteira e os indicadores de gestão não tenham sido quantificados.')
        if re.search(r'pedido',txt) and re.search(r'whatsapp',txt) and re.search(r'necessid|verific|indica|solicit',txt):
            items.append('No atendimento de pedidos pelo WhatsApp, a prática informada combina recebimento da solicitação, identificação da necessidade e encaminhamento do produto pretendido. A sequência é compatível com atendimento comercial, mas não demonstra, por si, domínio de conferência técnica ou dispensação de medicamentos.')
        if re.search(r'medicament|farmac',txt) and re.search(r'meta|venda',txt):
            items.append('A passagem pelo segmento farmacêutico foi relacionada a atendimento ao público e metas comerciais. Essa vivência aproxima o candidato da dinâmica de balcão, mas não permite atribuir atividades técnicas próprias de farmácia sem registro específico.')
        if re.search(r'caixa',txt) and re.search(r'atend|public|cliente',txt):
            items.append('A experiência em operação de caixa amplia o repertório em atendimento de rotina e contato direto com consumidores, embora as responsabilidades de fechamento e conferência de valores dependam de comprovação específica.')
        if re.search(r'planilha',txt) and re.search(r'prioriz|acompanha|retorno|agenda',txt):
            items.append('No controle da carteira, a organização de retornos por planilha e a priorização dos contatos indicam preocupação com continuidade das negociações. A qualidade desse controle depende de verificar periodicidade, critérios de atualização e resultados associados.')
        if re.search(r'entreg|motoboy',txt) and re.search(r'prazo|ordem|priorid',txt):
            items.append('Na operação de entregas, a organização de solicitações por sequência e a comunicação de prazos sugerem familiaridade com acompanhamento logístico e alinhamento de expectativas. Não há informação suficiente para concluir sobre controle de divergências, conferência de medicamentos ou autonomia na liberação dos pedidos.')
    return list(dict.fromkeys(items))[:3]


def _behavior_findings(answers):
    out=[]
    for answer in answers:
        txt=_normalize(answer)
        if re.search(r'escut|ouvi|ouvindo',txt) and re.search(r'indic|orient|produto|propost|explic',txt):
            out.append('A atenção às necessidades antes da orientação ou indicação de uma solução é compatível com escuta comercial e atendimento consultivo. O exemplo descreve uma conduta relevante, mas não permite concluir sobre sua consistência em situações de maior conflito ou pressão.')
        if re.search(r'instagram|promo|propaganda|folheto|folde',txt) and re.search(r'expli|orient|informa|educac',txt):
            out.append('No tratamento de dúvidas relacionadas às condições de divulgação de ofertas, houve referência à necessidade de explicar limites e prazos ao público. A situação é pertinente à comunicação clara e à condução de expectativas de clientes.')
        if re.search(r'prazo|ordem|prioriz',txt) and re.search(r'entrega|motoboy|equipe|agenda',txt):
            out.append('A organização da sequência de atendimento e a comunicação dos prazos indicam atenção à previsibilidade da operação e ao alinhamento com clientes ou colegas, aspectos que podem ser aprofundados em cenários de simultaneidade de demandas.')
        if re.search(r'urgente|imprevist|mudanc',txt) and re.search(r'replanej|prioriz|inform|avisa',txt):
            out.append('Em situação de mudança de prioridade, descreveu ajuste de planejamento e comunicação com os envolvidos. Há um exemplo de adaptação operacional, ainda sem elementos para generalizar o comportamento sob pressão.')
        if re.search(r'duvida|preocupa|objec',txt) and re.search(r'ouvi|escut|expli|alinh',txt):
            out.append('Diante de dúvidas do interlocutor, o encaminhamento descrito combinou escuta, esclarecimento e alinhamento de próximos passos. A atitude é pertinente a negociações consultivas, embora o resultado comercial do caso não esteja demonstrado.')
    return list(dict.fromkeys(out))[:3]


def _reviewed(report,category):
    selected=[c for c in _criteria(report,category) if c.get('review_decision') in ('ratificar','retificar')]
    high=[c for c in selected if c.get('score') is not None and c['score']>=3]
    partial=[c for c in selected if c.get('score') is not None and 1<=c['score']<=2]
    gaps=[c for c in selected if c.get('score')==0]
    return high,partial,gaps


def _safe_requirements(cs,limit=3):
    out=[]
    for c in cs:
        item=_clean(c.get('criterion',''),110)
        if item and item.casefold() not in [x.casefold() for x in out] and not GENERIC.search(item):out.append(item[0].lower()+item[1:])
        if len(out)>=limit:break
    return out


def _disc_summary(report,disc_text):
    if not str(disc_text or '').strip():return ''
    named=re.search(r'(?i)(?:perfil|estilo)\s*[:\-]?\s*([\wÀ-ÿ-]{4,30})',str(disc_text or '')[:5000])
    detail='O relatório DISC é utilizado como informação complementar sobre preferências comportamentais'
    if named and not PRIVATE.search(named.group(1)):
        detail+=' e apresenta a classificação '+_clean(named.group(1),38)
    detail+='. Suas tendências precisam ser confrontadas com ações relatadas na experiência profissional; o instrumento, isoladamente, não comprova desempenho, postura diante da pressão nem adequação à vaga.'
    return detail


def compose(report,cv='',linkedin='',disc='',narrative=''):
    job=_clean(report.get('job_title') or 'a oportunidade',100)
    tech=_criteria(report,('responsabilidade','hard'))
    soft=_criteria(report,('soft',))
    responses_t=_answers(tech)
    responses_s=_answers(soft)
    areas,employers=_career(cv,linkedin,narrative)
    separate=_activities('\n'.join(responses_t),8)
    narration_acts=_activities(narrative,6)
    t=[];b=[];rec=[]

    if areas:
        names=(' Passagens por '+_join(employers)+' fazem parte desse histórico.' if employers else '')
        t.append('O histórico profissional apresenta experiências em '+_join(areas[:4])+'.'+names+
            ' A correspondência com a posição de '+job+' é mais direta nas atividades de atendimento e operação efetivamente descritas, enquanto competências específicas da função exigem análise separada da experiência setorial.')
    else:
        t.append('A documentação disponível ainda não permite reconstituir com segurança a trajetória anterior em atividades relacionadas à posição de '+job+'. A ausência de registro suficiente limita o nível de conclusão sobre experiência específica.')
    # Relaciona ações à vaga sem reproduzir as palavras do candidato.
    if separate:
        t.append('No questionário, as situações profissionais descritas envolvem '+_join(separate[:6])+'. '+
             'Esse repertório é pertinente às etapas da função que compartilham essas atividades. A avaliação distingue familiaridade com a rotina de execução autônoma, especialmente quando faltam informações sobre frequência, processos utilizados e resultados obtidos.')
    else:
        t.append('As respostas do questionário não apresentam elementos operacionais suficientemente específicos para demonstrar como as atividades centrais foram realizadas. O nível de autonomia e os procedimentos precisam ser esclarecidos antes de considerar domínio técnico.')
    findings=_operational_findings(responses_t+[narrative])
    if findings:t.extend(findings)
    if narration_acts:
        extra=[a for a in narration_acts if a not in separate]
        if extra:
            t.append('A apresentação profissional acrescenta referências a '+_join(extra[:3])+'. Esses elementos complementam o histórico, mas permanecem declarações do candidato até que seu alcance e sua execução sejam confirmados.')
    high,partial,gaps=_reviewed(report,('responsabilidade','hard'))
    if high or partial:
        contents=[]
        if high:contents.append('maior consistência em '+_join(_safe_requirements(high,3)))
        if partial:contents.append('evidências parciais em '+_join(_safe_requirements(partial,2)))
        t.append('A avaliação consolidada pelo recrutador identificou '+ '; '.join(contents)+'. O grau de correspondência é apresentado de acordo com os exemplos existentes, sem converter uma atividade próxima em experiência comprovada em todos os procedimentos da vaga.')
    if gaps:
        t.append('Foram identificadas limitações específicas em '+_join(_safe_requirements(gaps,2))+'. A importância dessas diferenças depende de serem requisitos indispensáveis ou atividades passíveis de treinamento.')
    uncovered=[c for c in tech if not c.get('answer') and c.get('score') is None]
    if uncovered:
        top=_safe_requirements(uncovered,2)
        if top:t.append('Permanece sem avaliação suficiente a execução de '+_join(top)+'. A falta de evidência não deve ser confundida com ausência de competência.')

    # Comportamentos ancorados nas ações descritas, sem falas literais.
    all_text='\n'.join(responses_t+responses_s+[narrative])
    behavior_terms=[]
    norm=_normalize(all_text)
    if re.search(r'escut|ouvi|ouvindo|necessidad',norm):behavior_terms.append('escuta e busca de compreensão da demanda')
    if re.search(r'explic|orient|esclarec|inform|convers',norm):behavior_terms.append('comunicação e esclarecimento de informações')
    if re.search(r'ordem|prazo|organiza|agenda|prioriz',norm):behavior_terms.append('organização de prioridades e comunicação de prazos')
    if re.search(r'resolv|dificuldade|problema|reclama',norm):behavior_terms.append('tratamento de dificuldades no atendimento')
    if re.search(r'equipe|colega|trein|lider|coorden',norm):behavior_terms.append('interação com equipes')
    findings_soft=_behavior_findings(responses_t+responses_s+[narrative])
    if behavior_terms:
        b.append('As situações profissionais apresentadas permitem observar indícios de '+_join(behavior_terms[:4])+'. A análise considera as condutas descritas em contextos de trabalho, sobretudo a forma de orientar interlocutores, organizar solicitações e encaminhar necessidades. Essas referências dão suporte à avaliação, mas não demonstram por si só a repetição do comportamento em diferentes situações.')
    else:
        b.append('O material disponível ainda não apresenta exemplos comportamentais específicos suficientes para caracterizar a atuação diante de clientes, colegas ou situações de pressão. Atribuições profissionais e autodescrições não são utilizadas isoladamente para concluir sobre competências interpessoais.')
    if findings_soft:b.extend(findings_soft)
    high_s,partial_s,gaps_s=_reviewed(report,('soft',))
    if high_s or partial_s:
        parts=[]
        if high_s:parts.append('evidência mais consistente em '+_join(_safe_requirements(high_s,3)))
        if partial_s:parts.append('manifestação ainda parcial em '+_join(_safe_requirements(partial_s,2)))
        b.append('Na revisão das competências comportamentais, o recrutador reconheceu '+ '; '.join(parts)+'. Essas conclusões permanecem limitadas aos contextos profissionais efetivamente relatados.')
    elif soft and not responses_s:
        b.append('O questionário não reuniu exemplos específicos para todos os comportamentos exigidos pela vaga. A verificação em conversa dirigida ou situação prática permitirá confirmar essas dimensões.')
    disc_par=_disc_summary(report,disc)
    if disc_par:b.append(disc_par)

    strengths=_safe_requirements(high,3)
    # Evidência textual concreta sem revisão humana não vira avaliação alta.
    if not strengths:
        strength_topics=[x for x in separate if any(w in _normalize(x) for w in ('atend','comercial','pedido','orient','entrega','cliente','crm'))][:3]
        if strength_topics:rec.append('Para a vaga de '+job+', a proximidade profissional identificável está concentrada em '+_join(strength_topics)+'. O histórico oferece uma base relacionada às rotinas de atendimento, mas as informações ainda não sustentam, isoladamente, uma conclusão sobre domínio integral dos requisitos.')
        else:rec.append('Para a vaga de '+job+', a documentação examinada ainda não demonstra com consistência a execução das responsabilidades centrais. A conclusão deve permanecer condicionada à avaliação específica das atividades essenciais.')
    else:
        rec.append('Para a vaga de '+job+', a avaliação consolidada identifica correspondência profissional mais consistente em '+_join(strengths)+'. Essa aderência resulta da análise das experiências e ações relatadas, considerando suas limitações e os requisitos efetivos da posição.')
    if uncovered or gaps:
        limitations=_safe_requirements(gaps+uncovered,3)
        if limitations:rec.append('Os pontos que merecem aprofundamento são '+_join(limitations)+'. O impacto dessas lacunas deve ser definido conforme a necessidade de conhecimento prévio e as condições de treinamento oferecidas pela empresa.')
    elif partial:
        rec.append('Embora haja aproximação com a rotina, ainda existem requisitos com evidências parciais cuja execução independente precisa ser verificada na próxima etapa.')
    comment=str(report.get('reviewer_comment') or '').strip()
    if re.search(r'(?i)\bn[aã]o\s+(?:considero\s+)?apt[oa]|n[aã]o\s+recomendo|n[aã]o\s+avan[cç]',comment):
        rec.append('O recrutador registrou posicionamento desfavorável ao avanço nesta etapa, considerando a análise realizada.')
    elif re.search(r'(?i)\b(?:considero\s+\w+\s+)?apt[oa]\b|recomendo\s+(?:seguir|avan[cç]|encaminh)|seguir no processo|avan[cç]ar',comment):
        rec.append('O recrutador registrou posicionamento favorável ao avanço para a próxima etapa do processo seletivo, sujeito à conferência dos pontos de atenção identificados.')
    else:
        rec.append('O encaminhamento para a próxima etapa depende do posicionamento registrado pelo recrutador após a conferência das fontes e das exigências da vaga.')
    return {'tecnicas':t[:7], 'comportamentais':b[:5], 'recomendacao':'\n\n'.join(rec)}

"""Parecer profissional com trechos concretos e trilha interna de fontes.

Processamento determinístico, sem prometer raciocínio generativo em servidor Render.
Uma ocorrência localizada é um indício declarado, nunca uma confirmação externa.
Não atribui notas, não determina encaminhamento e não usa DISC como prova de desempenho.
"""
from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from behavioral_analysis import disc_paragraph, negated

STOP = set('sobre entre para pela pelas pelos quando como onde quais quais também ainda muito trabalho trabalhos profissional profissionais empresa empresas candidato candidato atividades atividade experiencia experiências experiência realizar realizando execução executar relacionado relacionadas importância responsabilidades responsabilidade conhecimento conhecimentos habilidade habilidades processo processos cliente clientes atua atuação tenho fazia fazer feito realizado realizar porque quanto dessa desse desta deste aqui quero queria pessoal minha minhas nossos suas dele tenho trabalho vaga posição'.split())
IGNORE = re.compile(r'(?i)(?:novo crit[eé]rio|inserir origem|pergunta\s+q\d+|an[eá]lise\s+do\s+sistema|teste gratuito|\b(?:https?://|www\.)|\b(?:cpf|rg|cnh)\s*[:=]|@|\b\d{11}\b|senha\s*[:=])')
PRIVATE = re.compile(r'(?i)\b(?:casad[oa]|solteir[oa]|divorciad[oa]|(?:meus?\s+)?filhos?|gravidez|idade|nasci|religião|partido|doença|diagnóstico|tratamento médico)\b')
ACTION = re.compile(r'(?i)\b(?:atendi|atendia|organizei|organizava|negociei|negociava|implantei|implementei|coordenei|liderava|lider[ei]|conferi|conferia|registrei|registrava|resolvi|resolvia|acompanhei|acompanhava|planejei|planejava|utilizei|utilizava|gerenciei|gerenciava|supervisionei|supervisionava|desenvolvi|desenvolvia|vendia|vendi|prospectava|prospectei|orientei|treinei|treinava|capacitei|reduzi|aumentei|fechei|faturamento|meta|crm|whatsapp|erp|excel|funil|projeto|cliente|processo|equipe)\b')
FAMILIES = (
    (r'atend|relacion|cliente|comunic|escut', r'atend|relacion|cliente|comunic|escut|convers|acolh|orient'),
    (r'vend|negoci|prospec|comercial|funil|crm', r'vend|negoci|prospec|comercial|funil|crm|lead|fech'),
    (r'confer|qualidade|inspe|medic|farmac|rotul', r'confer|qualidade|inspe|medic|farmac|rotul|chec|verific'),
    (r'obra|engenh|constr|orcament|projet|cronogram', r'obra|engenh|constr|orcament|projet|cronogram|planilh'),
    (r'market|campanh|conteud|trafeg|social', r'market|campanh|conteud|trafeg|social|public|midia'),
    (r'finance|concili|fatura|contab|cobranc', r'finance|concili|fatura|contab|cobranc|pagament'),
    (r'organiz|planej|process|prioriz|controle|disciplina', r'organiz|planej|process|prioriz|controle|monitor|registr'),
    (r'lider|gest|equipe|trein|colabor', r'lider|gest|equipe|trein|colabor|coorden|orient'),
    (r'desenvolv|python|dados|program|software|tecnolog', r'desenvolv|python|dados|program|software|tecnolog|sql'),
)


def normalized(value):
    text=unicodedata.normalize('NFKD',str(value or '').casefold())
    return ''.join(c for c in text if not unicodedata.combining(c))


def stems(value):
    return {w[:6] for w in re.findall(r'[a-z]{4,}',normalized(value)) if w not in STOP and len(w)>=4}


def normalize_for_display(text, limit=510):
    text=re.sub(r'\s+',' ',str(text or '')).strip(' \t\r\n\u2022-;,.')
    text=re.sub(r'(?i)[\w.+-]+@[\w-]+(?:\.[\w-]+)+','',text)
    text=re.sub(r'(?i)\b(?:\+?55\s*)?\(?\d{2}\)?\s*9?\d{4}[-\s]?\d{4}\b','',text)
    text=re.sub(r'\s{2,}',' ',text).strip(' .,;')
    if len(text)>limit: text=text[:limit].rsplit(' ',1)[0].rstrip(' .,;:')+'…'
    return text


def is_placeholder(text):
    return bool(IGNORE.search(text or ''))


def sentences(text):
    # PDFs e DOCXs podem produzir quebras em cada linha; processa parágrafos, períodos e itens.
    raw=str(text or '').replace('•','\n').replace('▪','\n').replace(' | ','\n')
    chunks=re.split(r'\n+|(?<=[.!?])\s+(?=[A-ZÀ-Ú])|;\s+',raw)
    out=[]
    for chunk in chunks:
        chunk=normalize_for_display(chunk,610)
        if not chunk or is_placeholder(chunk) or PRIVATE.search(chunk):continue
        if 37<=len(chunk)<=610 and len(chunk.split())>=6:
            out.append(chunk)
    return out[:250]


def relevance(segment, requirements, *, is_answer=False):
    text=normalized(segment)
    target=' '.join(normalized(x) for x in requirements)
    if not target:return 0
    overlap=len(stems(segment)&stems(target))
    family_matches=sum(bool(re.search(left,target) and re.search(right,text)) for left,right in FAMILIES)
    score=overlap*2+family_matches*2
    if ACTION.search(segment):score+=2
    if is_answer and len(segment.split())>=12:score+=1
    if re.search(r'\b(?:crm|excel|erp|power bi|python|whatsapp|salesforce|rd station|metas?|\d+\s*%)\b',text):score+=1
    return score


def select_passages(text,requirements,limit=2,*,is_answer=False,exclude=None):
    selected=[];used=exclude if exclude is not None else []
    ranked=[]
    for index,segment in enumerate(sentences(text)):
        if negated(segment):continue
        sc=relevance(segment,requirements,is_answer=is_answer)
        if sc<3:continue
        ranked.append((sc,-index,segment))
    for _,_,item in sorted(ranked,reverse=True):
        norm=normalized(item)
        if any(SequenceMatcher(None,norm,normalized(old)).ratio()>.77 for old in used):continue
        selected.append(item);used.append(item)
        if len(selected)>=limit:break
    return selected


def safe_criteria(report,category):
    return [c for c in (report.get('criteria') or [])
            if c.get('category_key') in category and c.get('criterion')
            and not is_placeholder(str(c.get('criterion')))]


def choose_answers(criteria, limit=3):
    result=[];seen=[]
    for item in criteria:
        answer=str(item.get('answer') or '').strip()
        if len(answer)<35 or is_placeholder(answer):continue
        answer=normalize_for_display(answer,440)
        if len(answer)<35 or PRIVATE.search(answer):continue
        if any(SequenceMatcher(None,normalized(answer),normalized(x)).ratio()>.8 for x in seen):continue
        seen.append(answer)
        specific=bool(ACTION.search(answer))
        is_negative=negated(answer)
        priority=relevance(answer,[item.get('criterion','')],is_answer=True)+(3 if specific else 0)
        if item.get('review_decision') in ('ratificar','retificar'):priority+=2
        result.append((priority,item,answer,is_negative))
    return [(c,a,n) for _,c,a,n in sorted(result,key=lambda x:-x[0])[:limit]]


def j(items):
    items=[str(x).strip(' .') for x in items if str(x).strip()]
    if not items:return ''
    if len(items)==1:return items[0]
    return ', '.join(items[:-1])+' e '+items[-1]


def _source_paragraph(source_name, passages, role, nearest=''):
    if not passages:return ''
    segments=['“'+p.rstrip('.;')+'”' for p in passages[:2]]
    cited=j(segments)
    relation=(' O vínculo com a posição de '+role+' aparece especialmente em '+nearest.lower()+'.' if nearest else '')
    if source_name=='Currículo':
        return ('O currículo registra '+cited+'.'+relation+
                ' O alcance dessas atividades precisa ser dimensionado pela participação efetiva, sem presumir indicadores de desempenho que não foram informados.')
    if source_name=='LinkedIn':
        return ('O histórico profissional no LinkedIn acrescenta '+cited+'.'+relation+
                ' Essas informações complementam a trajetória e ajudam a identificar experiências para aprofundamento, sem constituir comprovação independente dos resultados.')
    return ('Na apresentação profissional, o candidato relatou '+cited+'.'+relation+
            ' A narrativa permite compreender decisões e etapas da rotina segundo seu próprio relato, incluindo dependências entre áreas quando mencionadas.')


def _criterion_para(criterion, answer, behavior=False):
    name=normalize_for_display(criterion,135)
    if not name:return ''
    topic=name[0].lower()+name[1:]
    if negated(answer):
        return ('Em relação a '+topic+', informou a seguinte limitação: “'+answer.rstrip('.;')+'”. '
                'O ponto deve ser comparado com as exigências reais da função e com as possibilidades de integração.')
    if behavior:
        return ('Ao abordar '+topic+', descreveu o episódio: “'+answer.rstrip('.;')+'”. '
                'A conduta relatada permite discutir como lidou com essa situação, inclusive decisões, interlocutores e encaminhamento, quando presentes no exemplo. Não permite generalizar seu comportamento a outros cenários.')
    followup=' O caso apresenta etapas reconhecíveis de atuação e constitui base para uma avaliação técnica mais específica.' if ACTION.search(answer) else ' A descrição ainda não delimita claramente as etapas executadas pelo candidato.'
    if re.search(r'(?i)\b(?:reduzi|aumentei|fechei|melhorei|economizei|resultado|meta|faturamento|\d+\s*%)\b',answer):
        followup+=' Resultados informados pelo candidato devem ser contextualizados quanto ao período, à sua participação e às condições em que ocorreram.'
    return ('Ao detalhar '+topic+', informou: “'+answer.rstrip('.;')+'”.'+followup)


def enhance(draft,report,cv_text='',linkedin_text='',disc_text='',career_narrative_text=''):
    """Enriquece três blocos usando fontes independentes e registra procedência apenas internamente."""
    role=normalize_for_display(report.get('job_title') or 'a oportunidade',120)
    tcrit=safe_criteria(report,('responsabilidade','hard'))
    bcrit=safe_criteria(report,('soft',))
    treqs=[str(c['criterion']) for c in sorted(tcrit,key=lambda c:-int(c.get('weight') or 0))[:12]]
    breqs=[str(c['criterion']) for c in bcrit[:12]]
    # Quando o roteiro contém critérios genéricos, a fonte ainda precisa tratar das atribuições da vaga.
    requirements=treqs+([role] if role else [])
    used=[];trace=[];technical=[]
    for label,content,max_items in [('Currículo',cv_text,3),('LinkedIn',linkedin_text,2),('Apresentação profissional',career_narrative_text,2)]:
        passages=select_passages(content,requirements,max_items,exclude=used)
        if passages:
            # Passagens literais preservadas internamente para auditoria humana.
            trace.extend({'fonte':label,'trecho':p} for p in passages)
            nearest=''
            if treqs:
                best=max(treqs,key=lambda req:max(relevance(p,[req]) for p in passages))
                # Um mesmo setor não significa domínio do requisito (por exemplo,
                # "vendas B2B" não comprova gestão de CRM). Exigir pelo menos
                # dois termos significativos coincidentes para citar o critério.
                if max(len(stems(p)&stems(best)) for p in passages)>=2:
                    nearest=normalize_for_display(best,112)
            technical.append(_source_paragraph(label,passages,role,nearest))
    examples=choose_answers(tcrit,3)
    for criterion,answer,negative in examples:
        technical.append(_criterion_para(criterion['criterion'],answer))
        trace.append({'fonte':'Questionário da entrevista','criterio':criterion['criterion'],'trecho':answer,'negativa':negative})
    negatives=[(c,a) for c,a,n in examples if n]
    answered=[str(c.get('answer') or '').strip() for c in tcrit+bcrit if str(c.get('answer') or '').strip()]
    if answered and all(len(a.split()) < 5 for a in answered):
        draft['validacoes_tecnicas']=['As respostas são curtas demais para comprovar a execução das atividades. Solicitar situações reais, responsabilidades, métodos e resultados.']+(draft.get('validacoes_tecnicas') or [])[:3]
    if negatives:
        gap_labels=[normalize_for_display(c['criterion'],130).lower() for c,a in negatives[:2]]
        technical.append('Entre as lacunas expressamente relatadas estão '+j(gap_labels)+'. A ausência de experiência direta declarada deve ser ponderada conforme os requisitos obrigatórios da função e o treinamento disponível.')
    if not technical:
        technical.append('Não foi possível localizar experiências concretas relacionadas aos requisitos técnicos da vaga nas informações disponíveis. A análise necessita de exemplos de atuação, responsabilidades exercidas e resultados, sem atribuir deficiência profissional a essa ausência de informação.')

    behavioral=[];soft_answers=choose_answers(bcrit,2)
    for criterion,answer,negative in soft_answers:
        behavioral.append(_criterion_para(criterion['criterion'],answer,True))
        trace.append({'fonte':'Questionário da entrevista','categoria':'comportamental','criterio':criterion['criterion'],'trecho':answer,'negativa':negative})
    # Quando todas as perguntas são técnicas, buscar situação com ação concreta no histórico.
    if not behavioral:
        episodes=choose_answers(tcrit,1)
        for criterion,answer,negative in episodes:
            if not negative and ACTION.search(answer):
                behavioral.append('O exemplo profissional relacionado a '+normalize_for_display(criterion['criterion'],125).lower()+' inclui: “'+answer.rstrip('.;')+'”. Esse episódio oferece contexto para observar como a pessoa executa tarefas e interage com a rotina, sem presumir um traço comportamental permanente.')
    # Uso da leitura DISC preexistente com suas ressalvas psicométricas.
    if str(disc_text or '').strip():
        axes=[normalize_for_display(c['criterion'],100) for c in bcrit[:3]]
        disc_text_out,disc_pending=disc_paragraph(disc_text,report.get('disc'),axes)
        if disc_text_out:behavioral.append(disc_text_out)
        else:behavioral.append('Foi disponibilizado um relatório DISC, mas os indicadores presentes não permitiram uma leitura segura das dimensões. O laudo original precisa ser conferido antes de qualquer interpretação.')
        if disc_pending:draft['validacoes_comportamentais']=list(dict.fromkeys((draft.get('validacoes_comportamentais') or [])+[disc_pending]))[:4]
    # Complemento contextual baseado no histórico, sem confundir cargo com atributo psicológico.
    if behavioral and (cv_text or career_narrative_text):
        behavioral.append('A leitura comportamental deve ser confrontada com as situações de trabalho narradas e com as responsabilidades registradas no histórico. A descrição de um cargo, por si só, não comprova comunicação, organização, liderança ou reação à pressão.')
    if not behavioral:
        behavioral=['As fontes disponíveis não trazem episódios comportamentais suficientemente detalhados para concluir sobre as competências exigidas. É necessária investigação por situações reais de trabalho.']

    # Parecer de recomendação: síntese substantiva, ainda sem decisão automática de avançar.
    rec=[]
    source_coverage=[]
    if cv_text.strip():source_coverage.append('currículo')
    if linkedin_text.strip():source_coverage.append('histórico do LinkedIn')
    if career_narrative_text.strip():source_coverage.append('apresentação profissional')
    if any(c.get('answer','').strip() for c in tcrit+bcrit):source_coverage.append('questionário')
    if disc_text.strip():source_coverage.append('DISC')
    proven_topics=[normalize_for_display(c['criterion'],108).lower() for c,a,n in examples if not n and ACTION.search(a)][:3]
    if proven_topics:
        rec.append('Para a função de '+role+', as experiências mais pertinentes descritas pelo candidato se concentram em '+j(proven_topics)+'. Há exemplos que permitem discutir a execução de atividades centrais, embora o grau de autonomia, a frequência e os resultados ainda dependam de conferência.')
    else:
        rec.append('Para a função de '+role+', não foi possível identificar relatos suficientemente detalhados de execução das responsabilidades centrais. Isso caracteriza uma limitação da evidência disponível, e não um juízo de incapacidade profissional.')
    present_records=[name for name,txt in [('currículo',cv_text),('LinkedIn',linkedin_text),('apresentação profissional',career_narrative_text)] if txt.strip()]
    if present_records and proven_topics:
        rec.append('O histórico em '+j(present_records)+' amplia o contexto dos episódios descritos. A consistência da trajetória deve ser examinada à luz das experiências e atividades registradas, evitando atribuir ao candidato resultados ou domínio técnico apenas pela menção de ferramentas ou cargos.')
    elif present_records:
        rec.append('O histórico em '+j(present_records)+' oferece referências de atuação, mas ainda é necessário identificar episódios concretos relacionados às exigências de '+role+'.')
    if negatives:
        rec.append('A análise também deve considerar a experiência direta não informada ou expressamente limitada nas atividades mencionadas, distinguindo requisitos essenciais de conhecimentos que podem ser adquiridos na integração.')
    # Priorização real: no máximo duas validações e sem placeholders editoriais.
    validations=[]
    for item in (draft.get('validacoes_tecnicas') or [])+(draft.get('validacoes_comportamentais') or []):
        item=normalize_for_display(item,205)
        if item and not is_placeholder(item) and normalized(item) not in {normalized(x) for x in validations}:
            validations.append(item)
        if len(validations)>=2:break
    if validations:
        rec.append('Na próxima etapa, recomenda-se '+ '; '.join(x[:1].lower()+x[1:].rstrip(' .') for x in validations)+'.')
    # Não usurpar a decisão do recrutador nem inferi-la a partir de notas DISC.
    explicit=str(report.get('reviewer_comment') or report.get('client_recommendation') or '').strip()
    if explicit and not is_placeholder(explicit):
        rec.append('Registro do recrutador: '+normalize_for_display(explicit,950)+'.')
    else:
        rec.append('O encaminhamento à liderança ou a recomendação final dependem da conferência dessas informações e da decisão expressa do recrutador responsável.')
    draft['tecnicas']=technical[:8]
    draft['comportamentais']=behavioral[:5]
    draft['recomendacao']='\n\n'.join(rec)
    current=draft.get('auditoria_cruzamento') or {}
    current.update({'fontes':{
        'curriculo':bool(cv_text.strip()),'disc':bool(disc_text.strip()),
        'linkedin':bool(linkedin_text.strip()),'questionario':any(c.get('answer','').strip() for c in tcrit+bcrit),
        'transcricao_apresentacao':bool(career_narrative_text.strip())},
        'trechos_utilizados':trace,'redacao':'Parecer documental por regras, sujeito à revisão humana; sem inferência automática de desempenho'})
    draft['auditoria_cruzamento']=current
    draft['evidencias_tecnicas_internas']=list(draft.get('evidencias_tecnicas_internas') or [])+trace
    return draft

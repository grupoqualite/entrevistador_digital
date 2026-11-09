"""Integra as notas validadas, a trajetória, a entrevista e o DISC à minuta do cliente.

Mantém a metodologia/valores numéricos no relatório interno; sem modelo semântico
local, a redação continua documental e sempre requer revisão humana.
"""
from __future__ import annotations
import re
import unicodedata
from difflib import SequenceMatcher
from behavioral_analysis import compact, split_document, negated, disc_paragraph, AXES, _match_actions

STOP = {'realizar','executar','ter','atuar','atividades','conhecimentos','experiência','experiencia',
        'e','de','do','da','dos','das','para','com','em','as','os','a','o','ou','um','uma','no','na',
        'cliente','clientes','profissional','equipe','adequado','boa','capacidade','competência',
        'competencias','competência','responsável','requisitos','domínio','dominio'}

def _normalized(text):
    value=unicodedata.normalize('NFD',str(text or '').casefold())
    return ''.join(ch for ch in value if unicodedata.category(ch)!='Mn')


def _terms(text):
    raw=_normalized(text)
    return {x[:5] for x in re.findall(r'[a-z]{4,}',raw) if x not in STOP}


# Famílias semânticas restritas: usadas apenas para localizar trechos,
# nunca para atribuir nota a partir de palavras-chave.
SEMANTIC_FAMILIES=(
 (r'atend|cliente|balcao|orienta|escut', r'atend|cliente|balcao|orient|escut|ouvi|acolh'),
 (r'confer|verific|qualidade|medicament', r'confer|verific|chec|compar|revis|medicament'),
 (r'organiz|prioriz|planej', r'organiz|prioriz|planej|regist|controle'),
 (r'comunic|relacion|clareza', r'comunic|convers|explic|esclarec|inform|orient'),
 (r'negoci|venda|comercial|prospec', r'negoci|vend|fech|prospec|crm|funil'),
 (r'crm|funil|indicador|gestao', r'crm|funil|indicador|relatorio|acompanham'),
 (r'pedido|entrega|estoque', r'pedido|entrega|estoque|separ'),
 (r'obra|cronograma|orcamento', r'obra|cronograma|orcamento|execu|forneced'),
 (r'financeir|concili|fatura', r'financeir|concili|fatura|contas|pagament'),
)


def _relates(criterion,passage,category='hard'):
    ct=_terms(criterion);pt=_terms(passage)
    overlap=len(ct&pt)
    if overlap>=2:return True
    creq=_normalized(criterion);ptext=_normalized(passage)
    relevant_families=sum(bool(re.search(require,creq) and re.search(related,ptext)) for require,related in SEMANTIC_FAMILIES)
    if category=='soft':
        # A pergunta comportamental exige conduta concreta, não descrição do cargo.
        action=bool(re.search(r'(?i)\b(?:organizei|registrei|acompanhei|expliquei|orientei|conferi|verifiquei|decidi|resolvi|negociei|priorizei|comuniquei|alinhei|ouvi)\b',passage))
        return relevant_families>=1 and action
    return relevant_families>=1 and (overlap>=1 or relevant_families>=2)


def _current_score(c):
    action=c.get('review_decision')
    if action=='retificar':return c.get('human_score')
    if action=='ratificar':return c.get('auto_score')
    return None

def _is_reviewed(c):
    return c.get('review_decision') in ('ratificar','retificar')

def _is_negative(text):
    """Negação explícita da prática do requisito, sem confundir silêncio com falha."""
    return negated(text) or bool(re.search(
        r'(?i)\b(?:nunca (?:conferi|entreguei|executei|realizei|coordenei|gerenciei|participei|utilizei)'
        r'|não (?:conferi|entreguei|executei|realizei|coordenei|gerenciei|participei|utilizei)'
        r'|não (?:tenho|possuo) (?:vivência|prática)|não sei (?:usar|fazer))\b',str(text or '')))


def _source_for(c,cv,linkedin):
    """Documental/professional; never creates a quote that is not in its source."""
    answer=compact(c.get('answer'),700)
    if answer and _is_negative(answer):
        return 'entrevista',answer
    if answer and not _is_negative(answer) and _relates(c.get('criterion'),answer,c.get('category_key','hard')):
        return 'entrevista',answer
    best=(0,'','')
    target=_terms(c.get('criterion'))
    for source,text in [('curriculo',cv),('linkedin',linkedin)]:
        for p in split_document(text)[:80]:
            if _is_negative(p):continue
            shared=target&_terms(p)
            # Registros de carreira exigem mais correspondência do que uma palavra
            # isolada: pedido não comprova conferência de medicamentos, por exemplo.
            if len(shared)>=2 and _relates(c.get('criterion'),p,c.get('category_key','hard')) and len(shared)>best[0]:
                best=(len(shared),source,p)
    if best[0]>=1:return best[1],best[2]
    return None,''

def _label(c):
    label=compact(c.get('criterion'),155).rstrip(' .;:')
    return re.sub(r'(?i)\bwhatsapp\b','WhatsApp',label)

def _lower_label(c):
    v=_label(c)
    return (v[:1].lower()+v[1:]) if v else v

def _first_sentence(text,max_chars=180):
    text=compact(text,max_chars)
    if not text:return ''
    return text.rstrip(' ;,')

def _conclusion(c,source,text):
    name=_label(c)
    score=_current_score(c)
    justification=compact(c.get('review_justification') if c.get('review_decision')=='retificar' else c.get('auto_reason'),310)
    if score is None:
        return None,'Competência revisada sem elementos suficientes para uma conclusão fundamentada.'
    if score==0:
        if source and _is_negative(text):
            return f'Em relação a {_lower_label(c)}, foi indicada ausência de experiência direta. Essa lacuna deverá ser dimensionada de acordo com a exigência real da função e a possibilidade de treinamento.',None
        if justification and c.get('review_decision')=='retificar':
            return f'A avaliação de {_lower_label(c)} identificou uma limitação relevante, que precisa ser considerada na correspondência com a função. O contexto e o alcance dessa restrição devem ser confirmados.',None
        return None,'Avaliação de não atendimento sem evidência textual explícita ou justificativa suficiente.'
    if not text:
        return None,'A nota foi revisada, mas não há relato ou trecho documental suficiente para fundamentar a conclusão.'
    if _is_negative(text):
        return f'Quanto a {_lower_label(c)}, o profissional indicou experiência limitada ou não exercida diretamente. O grau de exigência desse conhecimento deverá orientar a necessidade de desenvolvimento.',None
    if source=='entrevista':
        # Entrevista não equivale a comprovação externa: linguagem de relato.
        if score>=3:
            return (f'Na dimensão de {_lower_label(c)}, há relato de atuação prática: {_first_sentence(text,205)}. '
                    'O conteúdo sustenta a avaliação favorável dessa atividade, condicionada à confirmação da autonomia e dos resultados apresentados.'),None
        if score==2:
            return (f'Quanto a {_lower_label(c)}, a experiência descrita indica correspondência parcial: {_first_sentence(text,185)}. '
                    'É necessário delimitar a frequência, a responsabilidade direta e o método aplicado.'),None
        return (f'Em {_lower_label(c)}, há referência à atividade, mas faltam exemplos de execução suficientes para dimensionar o domínio profissional.'),None
    if score>=3:
        # Não equipara documento a competência robusta por si só.
        return (f'O percurso profissional também situa {_lower_label(c)} entre as experiências registradas. '
                'A avaliação favorável requer confirmar a execução direta, pois os registros históricos, isoladamente, não demonstram o nível de domínio.'),None
    return (f'O histórico registra contato com {_lower_label(c)}, mas o material ainda não permite afirmar domínio integral da atividade ou independência na execução.'),None

def _trace(c,source,excerpt,category):
    return {'criterio':_label(c),'categoria':category,'origem':source or 'não evidenciada',
            'trecho':compact(excerpt,450),'nota_preliminar':c.get('auto_score'),
            'nota_revisada':_current_score(c),'decisao':c.get('review_decision'),
            'fundamento_revisao':compact(c.get('review_justification'),700)}

def _relevance(c,soft_text):
    target=_terms(c.get('criterion'));soft=_terms(soft_text)
    return len(target & soft)

def _discuss_disc(disc_text,disc_report,axes,evidence_text=''):
    if not str(disc_text or '').strip():return None,'A análise comportamental não dispõe de relatório DISC interpretável.'
    narrative,pend=disc_paragraph(disc_text,disc_report,axes)
    if narrative:
        # Comparação observável e limitada: episódios profissionais não confirmam
        # um traço DISC e pontuações do DISC não comprovam competências.
        evidence=str(evidence_text or '')
        relations=[]
        if re.search(r'(?i)\bestabilidade\s+(?:alta|elevada)\b',disc_text) and re.search(r'(?i)\b(?:acompanhei|organizei|planejei|registrava|monitorava|acompanhamento)\b',evidence):
            relations.append('a organização e o acompanhamento de atividades relatados permitem discutir a constância da atuação')
        if re.search(r'(?i)\bconformidade\s+(?:alta|elevada)\b',disc_text) and re.search(r'(?i)\b(?:verifiquei|conferi|comparei|revisei|chequei|corrigi|procedimentos?)\b',evidence):
            relations.append('a conferência de informações descrita oferece um exemplo de cuidado com procedimentos')
        if re.search(r'(?i)\bdominância\s+(?:baixa|reduzida)\b',disc_text) and re.search(r'(?i)\b(?:coordenei|cobrei|negociei|decidi|resolvi)\b',evidence):
            relations.append('as decisões e cobranças relatadas merecem consideração, evitando equiparar a dimensão do instrumento à falta de assertividade')
        if relations:
            narrative+=' Na experiência profissional, '+relations[0]+'. Trata-se de correspondência pontual, não de validação psicométrica.'
        return narrative,pend
    return ('O DISC integra o contexto da avaliação, mas as dimensões do instrumento não puderam ser relacionadas com segurança às condutas profissionais descritas. A leitura do laudo completo permanece necessária.',pend)

def integrate_draft(draft, report,cv_text='',linkedin_text='',disc_text=''):
    """Reescreve a análise a partir de critérios efetivamente revisados, com trilha interna.

    Sem revisão humana continua a minuta documental existente. Divergências
    entre nota e fonte são sinalizadas, jamais preenchidas por suposição.
    """
    criteria=report.get('criteria') or []
    if not any(_is_reviewed(c) for c in criteria):
        draft.setdefault('evidencias_tecnicas_internas',[])
        draft.setdefault('auditoria_cruzamento',{'criterios_revisados':0,'tecnicos':0,'comportamentais':0,'alertas':[]})
        return draft
    tech=[c for c in criteria if c.get('category_key') in ('responsabilidade','hard') and _is_reviewed(c)]
    soft=[c for c in criteria if c.get('category_key')=='soft' and _is_reviewed(c)]
    technical_trace=[];behavioral_trace=list(draft.get('evidencias_comportamentais_internas') or []);
    tech_paras=[];soft_paras=[];alerts=[]
    # Peso define somente relevância de seleção interna. Números não saem no PDF.
    for c in sorted(tech,key=lambda c:(bool(c.get('differential')), -int(c.get('weight') or 0))):
        source,excerpt=_source_for(c,cv_text,linkedin_text)
        paragraph,alert=_conclusion(c,source,excerpt)
        score=_current_score(c)
        if score is not None and score>=3 and (not excerpt or (_is_negative(excerpt))):
            alerts.append(f'{_label(c)}: revisão favorável sem relato positivo que a sustente.')
        if score==4 and excerpt and not re.search(r'(?i)\b(?:\d+(?:[,.]\d+)?%?|resultado|meta|entrega|fechamento|redução|aumento|melhoria|prazo)\b',excerpt):
            alerts.append(f'{_label(c)}: nível máximo requer contexto de resultado ou indicador que não foi identificado automaticamente.')
        technical_trace.append(_trace(c,source,excerpt,'técnica'))
        if alert:alerts.append(f'{_label(c)}: {alert}')
        if paragraph:tech_paras.append(paragraph)
        if len(tech_paras)>=4:break
    # Eixos comportamentais recebem evidências de qualquer pergunta, com
    # verificação de pertinência; disciplina, escuta etc. não se deduzem do cargo.
    all_answers=[(c,compact(c.get('answer'),700)) for c in criteria if c.get('answer')]
    for c in sorted(soft,key=lambda c:-int(c.get('weight') or 0)):
        score=_current_score(c)
        source,excerpt=_source_for(c,cv_text,linkedin_text)
        if not excerpt or _is_negative(excerpt):
            # Busca ações relacionadas em outros relatos; sem presumir que
            # competência comportamental se prove por uma palavra isolada.
            matching=[]
            for axis in AXES:
                if re.search(axis['relevance'],c.get('criterion') or '',re.I):
                    for other,a in all_answers:
                        acts=_match_actions(a,axis)
                        if acts and not _is_negative(a):matching.append((len(acts),a,other))
            if matching:
                _,excerpt,other=max(matching,key=lambda x:x[0]);source='entrevista (outra competência)'
        if score is None:
            alerts.append(f'{_label(c)}: avaliação humana sem nota e sem conclusão.');continue
        if score==0:
            if excerpt and _is_negative(excerpt):
                soft_paras.append(f'Quanto a {_lower_label(c)}, a experiência direta não foi demonstrada, exigindo validação proporcional ao contexto da função.')
            else:
                alerts.append(f'{_label(c)}: não atendimento indicado sem relato negativo explícito.')
        elif excerpt and source.startswith('entrevista'):
            desc=(_first_sentence(excerpt,185))
            qualifier=('oferece evidência favorável de comportamento aplicado em situação profissional' if score>=3
                       else 'permite reconhecer manifestação parcial, ainda insuficiente para generalizar o comportamento' if score==2
                       else 'apresenta contato com o tema, sem episódio suficientemente detalhado para uma conclusão forte')
            soft_paras.append(f'Em {_lower_label(c)}, a atuação descrita {qualifier}. O episódio inclui: {desc}. A consistência dessa conduta em outros contextos deverá ser confirmada.')
        elif excerpt:
            soft_paras.append(f'Em {_lower_label(c)}, o histórico oferece contexto profissional relevante. Ainda é necessário observar a conduta em episódios concretos, pois o cargo ou a atividade descrita não comprovam, isoladamente, a competência comportamental.')
        else:
            alerts.append(f'{_label(c)}: nota revisada sem episódio ou registro documental pertinente.')
        if score is not None and score>=3 and not excerpt:
            alerts.append(f'{_label(c)}: competência comportamental bem avaliada sem episódio registrado.')
        behavioral_trace.append(_trace(c,source,excerpt,'comportamental'))
        if len(soft_paras)>=3:break
    if tech_paras:
        old=draft.get('tecnicas') or []
        # Introdução de trajetória da minuta anterior permanece como contexto;
        # parágrafos avaliativos são reorganizados pelas evidências revisadas.
        draft['tecnicas']=(old[:1]+tech_paras)[:6]
    if soft_paras:
        axes=[_label(c) for c in soft[:3]]
        disc_par,disc_alert=_discuss_disc(disc_text,report.get('disc'),axes,' '.join(a for _,a in all_answers)+' '+cv_text)
        if disc_par:soft_paras.append(disc_par)
        if disc_alert:alerts.append(disc_alert)
        draft['comportamentais']=soft_paras[:5]
    elif soft and disc_text:
        # Mesmo sem episódios, DISC sozinho não gera parecer positivo.
        disc_par,_=_discuss_disc(disc_text,report.get('disc'),[],' '.join(a for _,a in all_answers)+' '+cv_text)
        if disc_par:draft['comportamentais']=(draft.get('comportamentais') or [])[:2]+[disc_par]
    # A recomendação resume apenas pontos apoiados em fontes e ratificados;
    # a decisão de encaminhamento permanece expressamente humana.
    validated_positive=[];validated_gaps=[]
    for c in tech+soft:
        note=_current_score(c)
        source,excerpt=_source_for(c,cv_text,linkedin_text)
        if note is not None and note>=3 and excerpt and not _is_negative(excerpt):
            validated_positive.append(_lower_label(c))
        if note==0 and (_is_negative(excerpt) or (c.get('review_decision')=='retificar' and c.get('review_justification'))):
            validated_gaps.append(_lower_label(c))
    supplement=[]
    if validated_positive:
        name='; '.join(validated_positive[:3])
        supplement.append(f'A aderência mais evidente se concentra em {name}, conforme o conjunto de experiências e relatos avaliados. Essa correspondência deve ser considerada nos limites da atuação efetivamente descrita.')
    if validated_gaps:
        name='; '.join(validated_gaps[:2])
        supplement.append(f'Persistem lacunas relevantes em {name}. A importância desses pontos depende de seu caráter obrigatório na função e das possibilidades de desenvolvimento.')
    if supplement:
        old_recommendation=draft.get('recomendacao') or ''
        draft['recomendacao']='\n\n'.join(supplement+[old_recommendation])
    # Não inferir recomendação a partir de score. Mantém decisão humana.
    draft['evidencias_tecnicas_internas']=technical_trace
    draft['evidencias_comportamentais_internas']=behavioral_trace
    draft['auditoria_cruzamento']={'criterios_revisados':len(tech)+len(soft),'tecnicos':len(tech),
        'comportamentais':len(soft),'disc_disponivel':bool(str(disc_text or '').strip()),
        'curriculo_disponivel':bool(str(cv_text or '').strip()),'linkedin_disponivel':bool(str(linkedin_text or '').strip()),
        'alertas':alerts}
    return draft

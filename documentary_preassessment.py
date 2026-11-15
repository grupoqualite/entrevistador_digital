"""Triagem preliminar documental, não é inteligência artificial nem pontuação.

Garante que mesmo sem Ollama as cinco fontes são examinadas e as razões de
não pontuação ficam explícitas. O recrutador decide e pode confrontar com IA
real quando um modelo está configurado.
"""
from __future__ import annotations
from narrative_upgrade import relevance, sentences, is_placeholder


def inspect(report, cv='', linkedin='', career='', disc=''):
    found=0
    for c in report.get('criteria',[]):
        requirement=c.get('criterion','')
        if is_placeholder(requirement):continue
        matches=[]
        if len(str(c.get('answer') or '').split())>=5:
            # A resposta é ligada a esta pergunta pelo próprio cadastro; não
            # corresponde a uma avaliação de proficiência.
            matches.append('resposta ao questionário')
        for label,txt in [('currículo',cv),('LinkedIn',linkedin),('apresentação profissional',career)]:
            relevant=[segment for segment in sentences(txt) if relevance(segment,[requirement])>=4]
            if relevant:matches.append(label)
        # DISC é somente contexto, não evidência de conhecimento ou competência.
        c['preliminary_sources']=matches
        if matches:
            c['preliminary_documentary_review']=(
                'O requisito possui referências relacionadas em '+', '.join(matches)+'. '
                'A localização textual não comprova execução independente, frequência ou resultados. '
                'A nota depende de avaliação contextual da situação profissional e revisão humana.')
            found+=1
        else:
            c['preliminary_documentary_review']=(
                'Não foram localizadas referências suficientemente relacionadas a este requisito nas fontes textuais disponíveis. '
                'Isso indica insuficiência documental, não ausência de competência.')
        if disc and c.get('category_key')=='soft':
            c['preliminary_documentary_review']+=' DISC disponível como contexto, sem uso para atribuição de nota.'
    report['documentary_preassessment']={
        'engine':'triagem_documental_por_regras_sem_pontuacao',
        'criteria_with_related_material':found,
        'total_criteria':len(report.get('criteria',[])),
        'sources':{'curriculo':bool(cv.strip()),'linkedin':bool(linkedin.strip()),
                   'apresentacao_profissional':bool(career.strip()),'disc':bool(disc.strip()),
                   'questionario':any(c.get('answer') for c in report.get('criteria',[]))},
        'nota':'A triagem não substitui avaliação da IA nem avaliação humana.'}
    return report

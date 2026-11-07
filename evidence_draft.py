"""Resumo documental rastreável para o plano sem modelo generativo.

Não atribui notas nem formula recomendações. Distingue respostas declaradas,
registros curriculares e dados ausentes; exige revisão editorial.
"""
from __future__ import annotations
import re
from engine import tokens


def _compact(value: str, length: int=350) -> str:
    s=re.sub(r"\s+", " ", str(value or "")).strip()
    if len(s)<=length:return s
    cut=s[:length].rsplit(" ",1)[0].rstrip('.,;:')
    return cut+'…'


def _safe_document_snippets(criteria, key):
    items=[]
    for c in criteria:
        for d in c.get('docs',[]):
            name=str(d.get('source',''))
            snippet=str(d.get('excerpt','')).strip()
            if (key=='cv' and name.lower().startswith('curr')) or (key=='linkedin' and name.lower().startswith('linkedin')):
                if snippet and snippet not in [z[1] for z in items]:items.append((c['criterion'],snippet))
    return items


def _interview_sentences(criteria, limit=6):
    out=[]
    for c in criteria:
        answer=str(c.get('answer') or '').strip()
        if len(answer)<18:continue
        out.append(f"Sobre {c.get('criterion','o requisito')}, o candidato informou: “{_compact(answer,310)}”.")
    return out[:limit]


def _grouped_paragraphs(sentences,max_sentences=2):
    return [' '.join(sentences[k:k+max_sentences]) for k in range(0,len(sentences),max_sentences)]


def draft_from_sources(report:dict, cv_text:str='',linkedin_text:str='',disc_text:str='') -> dict:
    criteria=report.get('criteria') or []
    technical=[c for c in criteria if c.get('category_key') in ('responsabilidade','hard')]
    behavioral=[c for c in criteria if c.get('category_key')=='soft']
    has_interview=any(str(c.get('answer') or '').strip() for c in criteria)
    has_cv=bool(str(cv_text or '').strip())
    has_li=bool(str(linkedin_text or '').strip())
    if not (has_interview or has_cv or has_li):
        raise ValueError('Não existem respostas transcritas nem texto extraído do currículo ou LinkedIn. Anexe os documentos e/ou conclua a entrevista antes de elaborar o parecer.')
    tech=[];behavior=[];pending_tech=[];pending_behavior=[]
    cv_found=_safe_document_snippets(technical,'cv')[:3]
    if cv_found:
        t=['No currículo, o requisito '+name+' aparece relacionado ao seguinte registro: “'+_compact(snippet,290)+'”.' for name,snippet in cv_found]
        tech.extend(_grouped_paragraphs(t,2))
    elif has_cv:
        tech.append('O currículo foi recebido e há texto extraído, mas os trechos disponíveis não foram vinculados de maneira segura às responsabilidades técnicas da vaga. É necessária leitura integral do histórico antes de concluir a aderência.')
        pending_tech.append('Conferir experiências e responsabilidades no currículo integral.')
    else:
        pending_tech.append('Anexar currículo legível para comparar trajetória, formação e responsabilidades.')
    li_found=_safe_document_snippets(technical,'linkedin')[:2]
    if li_found:
        t=['No perfil profissional exportado, consta: “'+_compact(snippet,240)+'”, em relação a '+name+'.' for name,snippet in li_found]
        tech.extend(_grouped_paragraphs(t,2))
    if not has_li and report.get('linkedin_url'):
        pending_tech.append('O endereço do LinkedIn não contém dados extraídos; solicitar o perfil exportado ou texto autorizado.')
    spoken=_interview_sentences(technical,6)
    tech.extend(_grouped_paragraphs(spoken,2))
    if not spoken:
        pending_tech.append('Entrevista sem respostas técnicas digitadas ou transcritas; não é possível avaliar a execução prática.')
    soft_spoken=_interview_sentences(behavioral,4)
    behavior.extend(_grouped_paragraphs(soft_spoken,2))
    if not soft_spoken:
        behavior.append('As respostas disponíveis não apresentam exemplos específicos suficientes para descrever competências comportamentais relacionadas à vaga. Essa análise permanece pendente de entrevista e revisão humana.')
        pending_behavior.append('Solicitar exemplos objetivos de organização, comunicação, autonomia ou outras competências descritas na vaga.')
    disc=report.get('disc') or {}
    obs=disc.get('observations') or []
    if disc_text.strip() and obs:
        desc=', '.join(str(x.get('dimension',''))+': '+str(x.get('reported_value','')) for x in obs[:6])
        behavior.append('O relatório DISC disponibilizado registra '+_compact(desc,350)+'. Esses indicadores são informações complementares e devem ser confrontados com comportamentos demonstrados em situações concretas, sem determinar a recomendação.')
    elif disc_text.strip():
        pending_behavior.append('Conferir o DISC original: não foi possível estruturar todas as dimensões automaticamente.')
    else:
        pending_behavior.append('DISC não fornecido ou sem texto extraível; não inferir resultados comportamentais do instrumento.')
    if not tech:
        tech=['Não há evidências técnicas suficientes para produzir uma análise conclusiva. O conteúdo da entrevista, currículo e perfil profissional deve ser conferido antes da recomendação.']
    return {'tecnicas':tech[:6],'comportamentais':behavior[:5], 'validacoes_tecnicas':pending_tech[:5],
            'validacoes_comportamentais':pending_behavior[:5],'recomendacao':'',
            'modo':'minuta documental sem avaliação semântica automática',
            'aviso':'Trechos extraídos e respostas declaradas, sem validação independente. Revise a redação e todas as evidências antes do envio.'}

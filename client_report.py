"""Parecer externo para o cliente: narrativa fundamentada, sem método de cálculo.

A trilha de pontuação e revisão permanece no relatório interno do produto.
A recomendação somente é publicada se registrada explicitamente pelo recrutador.
"""
from __future__ import annotations
import html
import io
import os
import re
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, KeepTogether, HRFlowable, Image, PageBreak, Table, TableStyle

ROOT=Path(__file__).resolve().parent
FONTS=[('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),
       ('/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf','/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf')]
FONT_NAME='Helvetica'; BOLD_NAME='Helvetica-Bold'
for normal,bold in FONTS:
    if Path(normal).exists() and Path(bold).exists():
        try:
            pdfmetrics.registerFont(TTFont('ClientRegular',normal))
            pdfmetrics.registerFont(TTFont('ClientBold',bold))
            FONT_NAME='ClientRegular'; BOLD_NAME='ClientBold'
            break
        except Exception:
            continue
NAVY=colors.HexColor('#0A3455')
INK=colors.HexColor('#26384A')
SUB=colors.HexColor('#596878')
RULE=colors.HexColor('#CFD7DE')
PAPER=colors.HexColor('#F4F7F9')
GOLD=colors.HexColor('#D5A836')


def _clean(s):
    """Remove conteúdo operacional de textos selecionados para circulação externa."""
    value=str(s or '').strip()
    # Redação destinada ao cliente jamais revela o mecanismo de análise.
    for pattern,repl in [
        (r'\b(?:IA|I\.A\.|Ollama|LLM|modelo de linguagem|inteligência artificial)\b','análise'),
        (r'\b(?:score_method|score de IA|nota automática|score automático)\b','avaliação'),
        (r'\b(?:ratifica(?:ção|da|do)|retifica(?:ção|da|do))\b','revisão'),
    ]:
        value=re.sub(pattern,repl,value,flags=re.I)
    return re.sub(r'\s+',' ',value).strip()


def _xml(s):
    return html.escape(_clean(s),quote=False)


def _find_explicit_review(report):
    return str(report.get('reviewer_comment') or report.get('client_recommendation') or '').strip()


def _groups(report):
    criteria=report.get('criteria') or []
    tech=[c for c in criteria if c.get('category_key') in ('responsabilidade','hard')]
    soft=[c for c in criteria if c.get('category_key')=='soft']
    return tech,soft


def _client_text_for_criterion(c):
    name=_clean(c.get('criterion') or 'Requisito profissional')
    expl=_clean(c.get('auto_reason'))
    if not c.get('verified_excerpts'):
        expl='Até o momento, não há exemplos suficientemente específicos de atuação que permitam concluir o nível de domínio desse requisito.'
    elif not expl or re.search(r'aguardando|não (?:há|houve) nota|descartada|modelo não',expl,re.I):
        expl='Há relatos relacionados à atividade, cuja profundidade deve ser conferida a partir das responsabilidades assumidas e dos resultados descritos.'
    excerpts=[]
    for q in c.get('verified_excerpts',[])[:2]:
        excerpt=_clean(q.get('excerpt',''))
        if excerpt:
            excerpt=excerpt.rstrip('.;')
            excerpts.append('“'+excerpt+'”')
    if excerpts:
        expl+=' Como referência, consta o seguinte relato: '+(' e '.join(excerpts))+'.'
    if c.get('differential'):
        name+=' (diferencial)'
    return name, expl


def _points(criteria,max_items=5):
    points=[]
    for c in criteria:
        for p in c.get('pending_validation',[])[:2]:
            v=_clean(p).removeprefix('Investigar: ').strip()
            if v and v.casefold() not in [z.casefold() for z in points]:points.append(v)
    return points[:max_items]


def render_client_pdf(report:dict, *, logo_path:str|Path|None=None, brand:str|None=None)->bytes:
    """Gera relatório com três seções executivas, sem notas por competência, rubrica ou fórmula.

    report['client_sections'] pode conter textos redigidos/revisados pelo recrutador:
      tecnicas: list[str], comportamentais: list[str], recomendacao: str,
      validacoes_tecnicas: list[str], validacoes_comportamentais: list[str]
    Quando ausente, usa apenas critérios, justificativas e citações registradas.
    """
    payload=report.get('client_sections') or {}
    brand=brand or os.environ.get('ENTREVISTADOR_MARCA','Entrevistador Digital')
    logo_path=Path(logo_path or os.environ.get('ENTREVISTADOR_LOGO_PDF') or str(Path(os.environ.get('ENTREVISTADOR_DATA',str(ROOT/'dados')))/'branding'/'logo.png'))
    buf=io.BytesIO()
    L,R,T,B=2.05*cm,2.05*cm,2.9*cm,2.0*cm
    doc=BaseDocTemplate(buf,pagesize=A4,leftMargin=L,rightMargin=R,topMargin=T,bottomMargin=B,
                        title='Parecer de Entrevista',author=_clean(brand))
    frame=Frame(L,B,A4[0]-L-R,A4[1]-T-B,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)

    styles={
        'heading':ParagraphStyle('client_heading',fontName=BOLD_NAME,fontSize=14,leading=18,textColor=NAVY,spaceAfter=10),
        'section':ParagraphStyle('client_section',fontName=BOLD_NAME,fontSize=10.7,leading=15,textColor=NAVY,spaceBefore=12,spaceAfter=6,keepWithNext=True),
        'sub':ParagraphStyle('client_sub',fontName=BOLD_NAME,fontSize=9.2,leading=13.2,textColor=NAVY,spaceBefore=7,spaceAfter=3,keepWithNext=True),
        'body':ParagraphStyle('client_body',fontName=FONT_NAME,fontSize=9.3,leading=15.0,alignment=TA_JUSTIFY,textColor=INK,spaceAfter=7,allowWidows=0,allowOrphans=0),
        'metadata':ParagraphStyle('client_meta',fontName=FONT_NAME,fontSize=8.8,leading=12.8,textColor=INK),
        'small':ParagraphStyle('client_small',fontName=FONT_NAME,fontSize=8,leading=12,alignment=TA_JUSTIFY,textColor=SUB,spaceAfter=5),
        'reco':ParagraphStyle('client_reco',fontName=FONT_NAME,fontSize=9.3,leading=15.0,alignment=TA_JUSTIFY,textColor=INK,spaceAfter=8),
    }
    story=[]
    def p(s,style='body'):
        return Paragraph(_xml(s),styles[style])
    def para(s,style='body'):
        if str(s or '').strip():story.append(p(s,style))
    def title(s):story.append(p(s,'section'))
    def sub(s):story.append(p(s,'sub'))
    def points(items):
        if items:
            sub('Pontos para validação')
            for item in items[:6]:para('• '+str(item),'small')
    story.append(p('PARECER DE ENTREVISTA','heading'))
    if report.get('client_preview'):
        story.append(p('MINUTA PARA REVISÃO. NÃO ENVIAR AO CLIENTE.','sub'))
    candidate=_clean(report.get('candidate') or 'Não informado')
    role=_clean(report.get('job_title') or 'Não informado')
    metadata=[[p('Candidato: '+candidate,'metadata')],[p('Vaga: '+role,'metadata')]]
    if report.get('linkedin_url'):metadata.append([p('LinkedIn: '+report['linkedin_url'],'metadata')])
    if report.get('client_salary_condition'):metadata.append([p('Condições informadas: '+report['client_salary_condition'],'metadata')])
    if report.get('review_status')=='Revisado pelo recrutador' and report.get('adherence_percent') is not None and report.get('coverage_percent',0)>=75:
        metadata.append([p('Aderência profissional: '+str(report['adherence_percent'])+'%','metadata')])
    if report.get('client_interview_date'):metadata.append([p('Entrevista: '+report['client_interview_date'],'metadata')])
    meta=Table(metadata,colWidths=[A4[0]-L-R],hAlign='LEFT')
    meta.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),PAPER),('LEFTPADDING',(0,0),(-1,-1),10),
                              ('RIGHTPADDING',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
    story.extend([meta,Spacer(1,5)])

    tech,soft=_groups(report)
    title('1. COMPETÊNCIAS TÉCNICAS')
    if payload.get('tecnicas'):
        for text in payload['tecnicas']:para(text)
    else:
        for section_name,items in [('Trajetória, responsabilidades e entregas',[c for c in tech if c.get('category_key')=='responsabilidade']),
                                   ('Conhecimentos e ferramentas',[c for c in tech if c.get('category_key')=='hard'])]:
            if items:
                sub(section_name)
                for c in items:
                    name,desc=_client_text_for_criterion(c)
                    para(name+'. '+desc)
        if not tech:para('Não há critérios técnicos avaliáveis registrados para esta vaga. É necessária revisão da descrição da oportunidade.')
    points(payload.get('validacoes_tecnicas',[]) if 'validacoes_tecnicas' in payload else _points(tech))

    title('2. COMPETÊNCIAS COMPORTAMENTAIS')
    if payload.get('comportamentais'):
        for text in payload['comportamentais']:para(text)
    else:
        if soft:
            sub('Evidências da entrevista')
            for c in soft:
                name,desc=_client_text_for_criterion(c)
                para(name+'. '+desc)
        else:para('Não existem evidências comportamentais suficientes para uma conclusão fundamentada nesta avaliação.')
        disc=report.get('disc') or {}
        if disc.get('observations'):
            sub('Leitura complementar do DISC')
            vals=[f"{x.get('dimension','')}: {x.get('reported_value','não informado')}" for x in disc['observations']]
            para('O material DISC apresenta os seguintes valores informados: '+', '.join(vals)+'. A interpretação desses indicadores deve ser contextualizada com o instrumento utilizado e com os comportamentos efetivamente observados na entrevista.','small')
        elif disc.get('status') and disc.get('status')!='não fornecido':
            sub('Leitura complementar do DISC')
            para('Os indicadores comportamentais ainda precisam ser examinados quanto à escala e às dimensões do DISC. A interpretação deve ser confrontada com situações profissionais concretas.','small')
    points(payload.get('validacoes_comportamentais',[]) if 'validacoes_comportamentais' in payload else _points(soft,3))

    title('3. PARECER DE RECOMENDAÇÃO')
    # Somente o recrutador define a recomendação; o indicador numérico não é veredito.
    recommendation=str(payload.get('recomendacao') or _find_explicit_review(report)).strip()
    if recommendation:
        for block in re.split(r'\n\s*\n',recommendation):
            para(block,'reco')
    else:
        para('Parecer de recomendação pendente de manifestação expressa do recrutador responsável. Os elementos técnicos e comportamentais apresentados devem ser revisados antes do envio ao cliente.','reco')
    if report.get('client_next_steps'):
        sub('Validações recomendadas na próxima etapa')
        para(report['client_next_steps'])
    story.append(Spacer(1,8))
    story.append(HRFlowable(width='100%',thickness=.55,color=RULE))
    if report.get('client_recruiter_name'):
        para('Responsável: '+report['client_recruiter_name'],'small')

    def decorate(canvas, doc):
        canvas.saveState()
        if logo_path.is_file():
            try:
                from PIL import Image as PILImage
                image=PILImage.open(logo_path)
                ratio=image.width/image.height
                w=4.0*cm;h=w/ratio
                canvas.drawImage(str(logo_path),L,A4[1]-1.43*cm-h/2,width=w,height=h,mask='auto',preserveAspectRatio=True)
            except Exception:canvas.setFont(BOLD_NAME,10);canvas.setFillColor(NAVY);canvas.drawString(L,A4[1]-1.6*cm,_clean(brand))
        else:
            canvas.setFont(BOLD_NAME,10);canvas.setFillColor(NAVY);canvas.drawString(L,A4[1]-1.6*cm,_clean(brand))
        canvas.setStrokeColor(GOLD);canvas.setLineWidth(1.1)
        canvas.line(L,A4[1]-2.2*cm,A4[0]-R,A4[1]-2.2*cm)
        canvas.setStrokeColor(RULE);canvas.setLineWidth(.55)
        canvas.line(L,1.45*cm,A4[0]-R,1.45*cm)
        canvas.setFont(FONT_NAME,7.4);canvas.setFillColor(SUB)
        canvas.drawString(L,1.08*cm,'Minuta não aprovada | Revisão pendente' if report.get('client_preview') else 'Parecer de entrevista | Uso profissional reservado ao cliente')
        canvas.drawRightString(A4[0]-R,1.08*cm,f'{doc.page}')
        canvas.restoreState()
    doc.addPageTemplates([PageTemplate(id='client',frames=frame,onPage=decorate)])
    doc.build(story)
    return buf.getvalue()

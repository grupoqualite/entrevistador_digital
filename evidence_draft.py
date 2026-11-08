"""Redação documental determinística e rastreável para a versão sem modelo de linguagem.

Nunca calcula nota nem deduz domínio de palavras-chave. Produz uma MINUTA de
parecer profissional a partir de declarações textuais e documentos recebidos.
A recomendação final e a publicação permanecem dependentes de confirmação humana.
"""
from __future__ import annotations
import re
from difflib import SequenceMatcher
from engine import tokens


def compact(value, limit=350):
    s=re.sub(r'\s+', ' ', str(value or '')).strip()
    if len(s)<=limit:return s
    prefix=s[:limit].rsplit(' ',1)[0].rstrip('.,;:')
    return prefix+'…'


def document_passages(criteria, source_name, limit=3):
    out=[];seen=set()
    for c in criteria:
        for d in c.get('docs',[]):
            if not str(d.get('source','')).lower().startswith(source_name):continue
            excerpt=str(d.get('excerpt') or '').strip()
            key=re.sub(r'\W+', '',excerpt.lower())[:110]
            if len(excerpt)<18 or key in seen:continue
            seen.add(key)
            out.append((str(c.get('criterion') or 'atribuição da vaga'),compact(excerpt,280)))
            if len(out)>=limit:return out
    return out


def distinct_answers(criteria, limit=5):
    """Evita transformar 12 respostas iguais em 12 aparentes evidências distintas."""
    out=[];seen=[];repeated=0
    for c in criteria:
        answer=str(c.get('answer') or '').strip()
        if len(answer)<18:continue
        criterion=str(c.get('criterion') or '').strip().rstrip('.,;:')
        normalized=re.sub(r'\W+',' ',answer.casefold().replace(criterion.casefold(),'')).strip()
        if any(SequenceMatcher(None,normalized,old).ratio()>=.81 for old in seen):
            repeated+=1
            continue
        seen.append(normalized)
        out.append((str(c.get('id','')),criterion,compact(answer,380)))
        if len(out)>=limit:break
    return out,repeated


def group(items,chunk=2):
    return [' '.join(items[i:i+chunk]) for i in range(0,len(items),chunk)]


def draft_from_sources(report:dict,cv_text:str='',linkedin_text:str='',disc_text:str='') -> dict:
    criteria=report.get('criteria') or []
    technical=[c for c in criteria if c.get('category_key') in ('responsabilidade','hard')]
    behavioral=[c for c in criteria if c.get('category_key')=='soft']
    tech_answers,repeated_tech=distinct_answers(technical,5)
    beh_answers,repeated_soft=distinct_answers(behavioral,3)
    has_cv=bool(str(cv_text or '').strip())
    has_li=bool(str(linkedin_text or '').strip())
    has_disc=bool(str(disc_text or '').strip())
    has_interview=any(str(c.get('answer') or '').strip() for c in criteria)
    if not (has_cv or has_li or has_interview):
        raise ValueError('Sem respostas escritas/transcritas nem texto extraído de currículo ou LinkedIn. Verifique os anexos e as respostas antes de preparar o dossiê.')

    tech=[];soft=[];pending_tech=[];pending_soft=[]
    cv_passages=document_passages(technical,'curr',3)
    li_passages=document_passages(technical,'linkedin',2)
    if cv_passages:
        snippets='; '.join('“'+snippet+'”' for _,snippet in cv_passages)
        tech.append('O currículo apresenta registros profissionais que se aproximam dos temas avaliados nesta vaga: '+snippets+'. Esses registros refletem informações documentais e precisam ser confrontados com a participação efetiva do candidato nas atividades relatadas.')
    elif has_cv:
        tech.append('O currículo foi anexado e contém texto extraível. Ainda não foi possível associar, com segurança, os registros profissionais às principais responsabilidades exigidas. A leitura do documento integral é necessária para determinar a extensão da experiência.')
        pending_tech.append('Conferir integralmente a trajetória, as datas e as atribuições descritas no currículo.')
    else:
        pending_tech.append('Currículo não recebido ou sem texto legível.')

    if li_passages:
        snippets='; '.join('“'+snippet+'”' for _,snippet in li_passages)
        tech.append('No perfil profissional exportado, aparecem os seguintes registros: '+snippets+'. Recomenda-se verificar a correspondência dessas informações com o currículo e com as declarações da entrevista.')
    elif report.get('linkedin_url') and not has_li:
        pending_tech.append('O link do LinkedIn está cadastrado, mas o conteúdo do perfil não foi extraído.')

    if tech_answers:
        items=[f'Quanto a {criterion}, na resposta {qid} o candidato declarou: “{answer}”.' for qid,criterion,answer in tech_answers]
        tech.extend(group(items,2))
        if repeated_tech:
            tech.append(f'Em outras {repeated_tech} resposta(s), o candidato utilizou relato substancialmente semelhante, sem acrescentar novos exemplos independentes sobre as demais atividades. A confirmação da profundidade técnica depende de casos específicos, responsabilidades e resultados.')
    else:
        pending_tech.append('As respostas técnicas estão ausentes ou foram curtas demais para demonstrar execução prática; solicitar exemplos específicos.')
    if not tech:tech.append('As fontes atuais não permitem descrever com segurança a experiência profissional relativa às responsabilidades e aos conhecimentos técnicos solicitados.')

    if beh_answers:
        items=[f'Sobre {criterion}, na resposta {qid} o candidato relatou: “{answer}”.' for qid,criterion,answer in beh_answers]
        soft.extend(group(items,2))
        if repeated_soft:
            soft.append(f'Em {repeated_soft} resposta(s) comportamentais, o relato foi substancialmente repetido; a repetição não comprova competências diferentes.')
        soft.append('Os relatos apresentados indicam situações para análise comportamental, mas sua consistência deve ser confrontada com as experiências profissionais e com exemplos verificáveis de atuação.')
    else:
        soft.append('O material disponível ainda não reúne exemplos comportamentais específicos suficientes para uma conclusão sobre as competências exigidas pela vaga. A ausência de resposta não demonstra ausência da competência.')
        pending_soft.append('Verificar exemplos concretos das competências comportamentais exigidas pela vaga.')

    disc=report.get('disc') or {}
    observations=disc.get('observations') or []
    if has_disc and observations:
        dimensions=', '.join(str(v.get('dimension',''))+': '+str(v.get('reported_value','não informado')) for v in observations[:6])
        soft.append('O relatório DISC fornecido registra '+compact(dimensions,350)+'. Esses dados devem ser interpretados conforme o instrumento aplicado e confrontados com os comportamentos relatados, sem servir isoladamente como medida de desempenho ou decisão de contratação.')
    elif has_disc:
        soft.append('Um relatório DISC foi disponibilizado, mas suas dimensões não puderam ser interpretadas com segurança a partir do texto extraído. É necessária a conferência visual do laudo original.')
        pending_soft.append('Ler o relatório DISC integral, incluindo legenda, escalas e contexto de aplicação.')
    else:
        pending_soft.append('Relatório DISC ausente ou sem conteúdo extraível. Não presumir características comportamentais.')

    key_activities=[]
    for c in technical:
        term=compact(c.get('criterion') or '',75).rstrip('.;:')
        if term and term.lower() not in [x.lower() for x in key_activities]:key_activities.append(term)
        if len(key_activities)==3:break
    role=compact(report.get('job_title') or 'a posição',100)
    if has_interview and (has_cv or has_li):
        intro='A documentação profissional e as respostas da entrevista oferecem informações para avaliar aspectos da candidatura à vaga de '+role+'.'
    elif has_interview:
        intro='As respostas da entrevista oferecem informações declaradas pelo candidato para examinar a candidatura à vaga de '+role+', mas a análise documental ainda é limitada.'
    else:
        intro='A documentação disponível oferece um ponto de partida para avaliar a candidatura à vaga de '+role+', porém faltam respostas de entrevista que demonstrem a execução prática das atribuições.'
    focus=(' Os principais pontos examinados são '+', '.join(key_activities)+'.') if key_activities else ''
    points=(pending_tech+pending_soft)[:3]
    validation=' Antes de uma recomendação conclusiva, é necessário '+('; '.join(points)).rstrip('. ') + '.' if points else ' Os relatos e registros devem ser validados pelo recrutador responsável.'
    recommendation=intro+focus+validation+' O encaminhamento para a próxima etapa deverá ser definido expressamente pelo recrutador após essa conferência.'
    return {
        'tecnicas':tech[:7], 'comportamentais':soft[:6],
        'validacoes_tecnicas':pending_tech[:5], 'validacoes_comportamentais':pending_soft[:5],
        'recomendacao':recommendation,
        'modo':'minuta documental baseada em fontes identificáveis',
        'aviso':'Minuta para conferência profissional. Não há atribuição automática de nota nem verificação independente das declarações.'
    }

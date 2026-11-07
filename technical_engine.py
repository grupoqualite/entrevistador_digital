"""Avaliação por evidências com IA local e homologação humana (V7).

Sem modelo local não há avaliação técnica automática: evita pontuação fictícia por palavras-chave.
A nota é um índice de aderência EVIDENCIADA (não uma previsão de desempenho ou aprovação).
"""
from __future__ import annotations
from datetime import datetime
from urllib.parse import urlsplit
import json, re, requests
from engine import norm, tokens, disc_summary, evidence_snippet

RUBRIC = {
 0:'Evidência explícita de não atendimento do critério; não equivale a ausência de informação',
 1:'Menção ao requisito, sem exemplo de aplicação',
 2:'Experiência parcial ou aplicação descrita, sem detalhes suficientes para confirmar domínio',
 3:'Exemplo específico, com participação pessoal, método e resultado descrito',
 4:'Exemplo específico, métodos e responsabilidades claras, resultado verificável ou indicador contextualizado',
}


def clean_quote(s):
    return re.sub(r'\s+',' ',str(s or '')).strip().casefold()


def evidence_is_in_source(quote, source):
    """Garantia de citação literal da fonte. Não prova que a declaração é verdadeira."""
    q=clean_quote(quote)
    return len(q)>=12 and q in clean_quote(source)


def metrics(report):
    """Denominador FIXO: não se renormaliza removendo critérios sem evidência.
    Critérios sem evidência ficam nulos, com cobertura explicita separada.
    """
    criteria=report.get('criteria',[])
    total_core_w=sum(int(c['weight']) for c in criteria if c.get('category_key') in ('responsabilidade','hard','soft') and not c['differential'])
    for c in criteria:
        c['weight_percent']=round(100*int(c['weight'])/total_core_w,1) if total_core_w and not c['differential'] else None
        c['score']=c.get('human_score') if c.get('review_decision')=='retificar' else c.get('auto_score')
    def group(pred):
        cc=[c for c in criteria if pred(c)]
        denom=sum(max(0,int(c['weight'])) for c in cc)
        evaluated=sum(max(0,int(c['weight'])) for c in cc if c['score'] is not None)
        if not denom:return {'score':None,'coverage':0,'weight':0,'assessed_weight':0}
        # Esconder a nota enquanto não houver uma única evidência avaliável.
        score=round(100*sum(int(c['weight'])*c['score'] for c in cc if c['score'] is not None)/(4*denom)) if evaluated else None
        return {'score':score,'coverage':round(100*evaluated/denom),'weight':denom,'assessed_weight':evaluated}
    technical=group(lambda c:c.get('category_key') in ('responsabilidade','hard') and not c['differential'])
    behavioral=group(lambda c:c.get('category_key')=='soft' and not c['differential'])
    total=group(lambda c:c.get('category_key') in ('responsabilidade','hard','soft') and not c['differential'])
    differential=group(lambda c:c['differential'])
    report.update({'technical_percent':technical['score'],'technical_coverage':technical['coverage'],
       'behavioral_percent':behavioral['score'],'behavioral_coverage':behavioral['coverage'],
       'adherence_percent':total['score'],'coverage_percent':total['coverage'],
       'differential_percent':differential['score'],'differential_coverage':differential['coverage'],
       'adherence_with_differentials_percent':None,
       'score_method':'Índice de aderência evidenciada: soma(peso × nota 0–4)/(4 × soma dos pesos da matriz), ×100. Critérios sem evidência não recebem nota nem saem do denominador. Não representa incapacidade nem aprovação.'})
    report['reviewed_count']=sum(1 for c in criteria if c.get('review_decision') in ('ratificar','retificar'))
    report['reviewable_count']=sum(1 for c in criteria if c.get('category_key') in ('responsabilidade','hard','soft'))
    report['review_status']='Revisado pelo recrutador' if report['reviewable_count'] and report['reviewed_count']==report['reviewable_count'] else ('Revisão parcial' if report['reviewed_count'] else 'Pendente de revisão humana')
    return report


def prepare_report(questions,answers,cv,disc,linkedin_text,linkedin_url,title,candidate,job_desc):
    """Coleta fontes por critério SEM atribuir notas por densidade/termos."""
    criteria=[];pending=[]
    for q in questions:
        a=answers.get(q['id'],{})
        answer=(a.get('text') or a.get('transcript') or '').strip()[:6000]
        terms=tokens(q.get('criterion',''))
        doc_hints=[]
        for source,content in [('Currículo',cv),('LinkedIn exportado',linkedin_text)]:
            if len(terms & tokens(content))>=max(1,min(2,len(terms))):
                extract=evidence_snippet(content,terms)
                if extract:doc_hints.append({'source':source,'excerpt':extract,'classification':'localização textual, não avaliação'})
        if a.get('audio_file') and not answer:pending.append('Áudio '+q['id']+' gravado e ainda não transcrito: conteúdo não analisado.')
        criteria.append({'id':q['id'],'category_key':q.get('category','hard'),
            'category':q.get('category_label',q.get('category','hard')),'criterion':q.get('criterion',''),
            'source_jd':q.get('origin',''), 'differential':bool(q.get('differential',False)),
            'weight':int(q.get('weight',2)), 'score':None,'auto_score':None,'human_score':None,
            'review_decision':'pendente','review_justification':'','status':'Aguardando avaliação contextual fundamentada',
            'docs':doc_hints,'verified_excerpts':[],'answer':answer,
            'answer_mode':a.get('mode','não respondida'),
            'notes':[],'pending_validation':[],
            'auto_reason':'Aguardando avaliação contextual por IA local. Palavras-chave não atribuem notas.',
            'method':'não avaliado'})
    if linkedin_url and not linkedin_text.strip():pending.append('O endereço do LinkedIn foi cadastrado, mas seu conteúdo não foi extraído. Envie o perfil exportado ou informações autorizadas.')
    if not cv.strip():pending.append('Currículo não disponível ou sem texto extraível.')
    if not disc.strip():pending.append('DISC não disponível ou sem texto extraível; não integra a nota.')
    if not criteria:pending.append('A descrição da vaga não gerou critérios suficientes. Revise o roteiro.')
    report={
        'candidate':candidate,'job_title':title,'generated_at':datetime.now().isoformat(timespec='seconds'),
        'analysis_mode':'Fontes e roteiro preparados, sem nota automática. Ative Ollama local para avaliação contextual.',
        'criteria':criteria,'disc':disc_summary(disc),'linkedin_url':linkedin_url,
        'linkedin_content_analyzed':bool(linkedin_text.strip()),'pendencias':pending,
        'rubric':RUBRIC,'review_history':[],'llm_summary':'',
        'automatic_approval':False,'eliminatorios_sugeridos':[],
        'conclusion':'Índice preliminar de aderência demonstrada, sujeito à conferência de fontes e ratificação ou retificação humana. Nenhuma aprovação ou reprovação automática.'}
    return metrics(report)


def quote_has_relevance(criterion,quote):
    """Barreira conservadora: uma citação literal sobre outro tema não serve de evidência.
    Aproximar raízes de palavras; sem substituir interpretação semântica do avaliador.
    """
    generic={'experiencia','experiencias','responsavel','realizar','realizada','realizado','fazer',
             'dominio','conhecimento','habilidade','competencia','experiente','pratica','atividade',
             'atividades','capacidade','profissional','trabalhar','trabalho','exemplo','requisitos',
             'comprovada','comprovacao','parte','contexto','resultados'}
    req={x[:5] for x in tokens(criterion) if x not in generic}
    found={x[:5] for x in tokens(quote) if x not in generic}
    return bool(req & found) if req else True


def local_url(url):
    p=urlsplit(url)
    if p.scheme!='http' or p.hostname not in ('localhost','127.0.0.1','::1'):
        raise ValueError('Ollama deve ser executado localmente (localhost), sem envio de documentos a servidor externo.')
    return url.rstrip('/')


def evaluate_with_ollama(report,cv,linkedin_text,job_desc,model,url='http://127.0.0.1:11434'):
    """Converte textos e transcrições em notas com evidências literais auditáveis.
    Sem citação literal existente a nota é descartada em vez de presumida.
    """
    endpoint=local_url(url)
    compact=[{'id':c['id'],'categoria':c['category_key'],'requisito':c['criterion'],
               'origem_vaga':c['source_jd'][:450],'peso':c['weight'],
               'resposta_entrevista':c['answer'][:2400]} for c in report['criteria']]
    payload={'descricao_vaga':job_desc[:9000], 'curriculo':cv[:12000],
            'linkedin_exportado':linkedin_text[:6000], 'criterios':compact}
    prompt='''Você é um avaliador técnico de recrutamento. Analise a ADERÊNCIA PROFISSIONAL por critério com base em currículo, entrevista transcrita e LinkedIn exportado. Não avalie por palavras-chave, extensão ou fluência do relato. Examine o conteúdo e a correspondência com a responsabilidade, hard skill ou soft skill EXATA da vaga. Não invente ferramentas, datas, resultados ou competências; não extrapole o DISC e não use o DISC para pontuação.
REGRA CRÍTICA: toda nota requer ao menos uma citação LITERAL, copiada EXATAMENTE dos textos das fontes fornecidas, no campo evidencias. Se nada demonstrar competência, retorne nota null. Uma ausência de menção NÃO é nota zero. Diferencie 'declaração do candidato' de resultado confirmado. Currículo sozinho pode sustentar no máximo nota 2; sem entrevista não deduza domínio prático. Diferenciais jamais devem se tornar obrigatórios. Avalie também o que falta validar.
RÚBRICA: 0=declaração explícita de não atender ao requisito, 1=mera menção, 2=aplicação parcial ou insuficientemente detalhada, 3=caso concreto com ação pessoal, método e resultado descrito, 4=caso concreto detalhado com método, contribuição própria e resultado mensurável/contextualizado. Nota 4 somente com evidência clara de método e resultado. 'Fiz vendas' é menção, não nota 4.
Use o conteúdo de UMA resposta para cada competência, evite atribuir a mesma experiência genérica a requisitos distintos sem justificativa. Avalie soft skills por comportamentos descritos, não por DISC.
Responda SOMENTE em JSON válido com: {"avaliacoes":[{"id":"Q01","nota":3,"justificativa":"...","evidencias":[{"fonte":"entrevista","trecho":"citação LITERAL da resposta"}],"lacunas":["..."],"pergunta_validacao":"..."}],"sintese":"...","eliminatorios":[{"requisito":"...","estado":"atende|não atende|não confirmado","fundamento":"..."}]}. Fonte SOMENTE 'entrevista', 'curriculo' ou 'linkedin'; nunca fonte 'disc'. Para nota null, evidencias pode ser []. Retorne um registro para cada ID, inclusive inconclusivos. Não dê veredito de aprovado/reprovado.'''
    r=requests.post(endpoint+'/api/generate',json={'model':model,'prompt':prompt+'\nDADOS: '+json.dumps(payload,ensure_ascii=False), 'format':'json','stream':False,'options':{'temperature':0,'num_ctx':16384}},timeout=300)
    r.raise_for_status()
    parsed=json.loads(r.json()['response'])
    if not isinstance(parsed,dict):raise ValueError('O modelo retornou formato inesperado.')
    byid={c['id']:c for c in report['criteria']}
    received=set();accepted=0;rejected=0
    for ev in parsed.get('avaliacoes',[]):
        if not isinstance(ev,dict):continue
        c=byid.get(ev.get('id'))
        if not c or c['id'] in received:continue
        received.add(c['id'])
        rating=ev.get('nota')
        if type(rating) is not int or rating<0 or rating>4:
            c['auto_reason']='Modelo não apresentou uma nota válida e justificável.'
            continue
        srcs={'entrevista':c.get('answer',''),'curriculo':cv[:12000],'linkedin':linkedin_text[:6000]}
        accepted_quotes=[]
        for quote in ev.get('evidencias',[]):
            if not isinstance(quote,dict):continue
            source=quote.get('fonte');fragment=str(quote.get('trecho','')).strip()
            if source in srcs and evidence_is_in_source(fragment,srcs[source]) and quote_has_relevance(c['criterion'],fragment):
                accepted_quotes.append({'source':source,'excerpt':fragment[:500],'type':'declaração/localização literal; não comprovação externa'})
        if not accepted_quotes:
            c['auto_reason']='Nota descartada: a IA não citou trecho literal e relevante para este critério. Conferir manualmente possíveis sinônimos ou evidências não capturadas.'
            rejected+=1;continue
        # Somente currículo / LinkedIn não justifica domínio avançado sem exemplo na entrevista.
        interview_cited=any(x['source']=='entrevista' for x in accepted_quotes)
        if not interview_cited and rating>2:
            rating=2
        c['auto_score']=rating
        c['verified_excerpts']=accepted_quotes[:5]
        c['auto_reason']=str(ev.get('justificativa','')).strip()[:1300] or 'Citações fornecidas; revisar contextualização.'
        c['pending_validation']=[str(x)[:250] for x in (ev.get('lacunas') or []) if isinstance(x,str)][:5]
        followup=ev.get('pergunta_validacao')
        if isinstance(followup,str) and followup.strip():c['pending_validation'].append('Investigar: '+followup[:300])
        c['status']='Nota preliminar proposta pela IA local, com trechos literais conferidos.'
        c['method']='IA local com fonte textual rastreável, sujeita à revisão humana'
        accepted+=1
    if not received:raise ValueError('O modelo não retornou avaliações para os critérios da vaga.')
    report['analysis_mode']=f'Análise técnica preliminar: Ollama local ({model}), com validação de trechos literais (não confirmação externa).'
    report['llm_summary']=str(parsed.get('sintese','')).strip()[:2400]
    report['model_review']={'model':model,'criteria_evaluated':accepted,'notes_rejected_for_lack_of_quotes':rejected,'criteria_total':len(byid)}
    report['eliminatorios_sugeridos']=[x for x in parsed.get('eliminatorios',[]) if isinstance(x,dict)][:15]
    if rejected:report['pendencias'].append(f'{rejected} nota(s) sem citação literal foram descartadas, aguardando avaliação humana.')
    if len(received)<len(byid):report['pendencias'].append('A IA não retornou todos os critérios da vaga; itens restantes permanecem sem nota.')
    return metrics(report)


def update_review(report,decisions,comment=''):
    if not isinstance(decisions,dict):raise ValueError('Decisões inválidas.')
    known={c['id']:c for c in report['criteria']}
    # Validar todas as revisões primeiro, sem alterações parciais em caso de erro
    pending=[]
    for ident,decision in decisions.items():
        if ident not in known:raise ValueError('Critério de avaliação não encontrado: '+str(ident))
        if not isinstance(decision,dict):raise ValueError('Decisão inválida para '+ident)
        action=decision.get('action','pendente')
        if action=='pendente':continue
        if action not in ('ratificar','retificar'):raise ValueError('Ação desconhecida para '+ident)
        row=known[ident]
        if action=='ratificar':
            if row.get('auto_score') is None:raise ValueError('Não é possível ratificar uma nota automática inexistente. Use retificar com justificativa.')
            score=row['auto_score']
        else:
            score=decision.get('score')
            if score is not None and (type(score) is not int or not (0<=score<=4)):
                raise ValueError('Nota humana deve ser 0–4 ou sem nota.')
            justification=str(decision.get('justification','')).strip()
            if len(justification)<15:raise ValueError('A retificação exige justificativa com ao menos 15 caracteres para '+ident)
        if row.get('review_decision')==action and (action=='ratificar' or (row.get('human_score')==score and row.get('review_justification')==str(decision.get('justification','')).strip())):
            continue  # Salvar novamente não duplica auditoria sem mudança
        pending.append((row,action,score,str(decision.get('justification','')).strip()[:2000]))
    ts=datetime.now().isoformat(timespec='seconds')
    for c,action,score,justification in pending:
        history={'id':c['id'],'date':ts,'decision':action,'previous_score':c.get('score'),
                 'auto_score':c.get('auto_score'),'human_score':score if action=='retificar' else None,
                 'justification':justification or 'Nota automática ratificada após conferência das fontes.'}
        report.setdefault('review_history',[]).append(history)
        c['review_decision']=action
        c['human_score']=score if action=='retificar' else None
        c['review_justification']=history['justification']
        c['reviewed_at']=ts
        c['status']='Nota ratificada pelo recrutador' if action=='ratificar' else 'Nota retificada pelo recrutador'
    report['reviewer_comment']=str(comment).strip()[:6000]
    if pending:report['reviewed_at']=ts
    return metrics(report)

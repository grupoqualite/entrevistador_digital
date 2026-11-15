"""Testes de regressão da evolução 9.7.7, com candidato inteiramente fictício."""
import os
from pathlib import Path
from technical_engine import prepare_report
from evidence_draft import draft_from_sources
from client_report import render_client_pdf


def demo():
    q=[
      {'id':'Q01','category':'responsabilidade','category_label':'Responsabilidades','criterion':'Realizar prospecção ativa e qualificação de leads','origin':'Prospecção ativa e qualificação de leads','weight':5,'differential':False},
      {'id':'Q02','category':'hard','category_label':'Hard skills','criterion':'Gerenciar CRM, funil e propostas comerciais','origin':'CRM, funil e propostas','weight':5,'differential':False},
      {'id':'Q03','category':'soft','category_label':'Soft skills','criterion':'Comunicação consultiva e escuta do cliente','origin':'Comunicação consultiva','weight':4,'differential':False},
      {'id':'Q04','category':'soft','category_label':'Soft skills','criterion':'Organização de rotinas e priorização','origin':'Organização e priorização','weight':4,'differential':False},
    ]
    answers={
      'Q01':{'text':'Eu prospectei empresas por telefone e WhatsApp, identifiquei o decisor e marquei reuniões quando havia interesse na solução. Acompanhava a resposta do cliente até o próximo contato.', 'mode':'text'},
      'Q02':{'text':'Utilizei RD Station CRM para registrar cada lead e organizar as etapas do funil. Atualizava propostas e acompanhava negociações semanais com a coordenação comercial.', 'mode':'text'},
      'Q03':{'text':'Conversei com um cliente que estava em dúvida entre duas propostas. Ouvi as preocupações, expliquei as diferenças e alinhei o próximo passo para avaliação interna.', 'mode':'text'},
      'Q04':{'text':'Eu priorizei contatos conforme a data da proposta e organizei uma planilha de acompanhamento de retornos. Quando surgiu uma demanda urgente, replanejei a agenda e informei a equipe.', 'mode':'text'},
    }
    cv=('Atuou como consultor comercial na Energia Exemplo entre 2022 e 2024, conduzindo prospecção de novos clientes, qualificação de leads e elaboração de propostas consultivas.\n'
        'Na Organização Exemplo trabalhou com ferramentas de CRM, acompanhamento do funil e atividades de pós-venda em contas empresariais.\n')
    linkedin=('No perfil LinkedIn informa atuação com vendas consultivas B2B e capacitação de integrantes de uma equipe comercial.\n'
              'Relata experiência no atendimento a clientes corporativos e condução de reuniões de apresentação de serviços.\n')
    narration=('Durante a apresentação profissional, relatei a organização de um fluxo de propostas que reduziu o atraso de respostas dos vendedores.\n'
               'Também expliquei que acompanhava negociações de médio prazo e precisava consultar a equipe de operações antes de confirmar prazos aos clientes.\n')
    disc='Perfil: Influenciador. Dominância D4, Influência I7, Estabilidade S3, Conformidade C2. Escala depende do laudo aplicado.'
    report=prepare_report(q,answers,cv,disc,linkedin,'https://www.linkedin.com/in/exemplo','Inside Sales','Candidato Fictício','Prospecção comercial com CRM, qualificação de leads e atendimento consultivo.')
    draft=draft_from_sources(report,cv,linkedin,disc,narration)
    return draft,report


def test_five_sources_have_provenance_and_three_sections():
    draft,report=demo()
    assert draft['tecnicas'] and draft['comportamentais'] and draft['recomendacao']
    coverage=draft['auditoria_cruzamento']['fontes']
    assert all(coverage.values()),coverage
    traces=draft['auditoria_cruzamento']['trechos_utilizados']
    assert {x['fonte'] for x in traces} >= {'Currículo','LinkedIn','Apresentação profissional','Questionário da entrevista'}
    text=' '.join(draft['tecnicas']+draft['comportamentais'])
    assert 'Energia Exemplo' in text
    assert 'propostas' in text
    assert 'DISC' in text
    assert 'Novo critério, inserir origem e competência' not in text
    assert 'Pergunta Q01' not in text
    assert report['adherence_percent'] is None  # O motor documental não inventa nota


def test_pdf_three_sections_and_independent_logo(tmp_path):
    import fitz
    draft,report=demo()
    report['client_sections']={k:draft[k] for k in ('tecnicas','comportamentais','recomendacao')}
    report['client_sections'].update({'validacoes_tecnicas':draft['validacoes_tecnicas'],'validacoes_comportamentais':draft['validacoes_comportamentais']})
    report['client_preview']=True
    original=render_client_pdf(report, logo_path=tmp_path/'sem-logo.png')
    assert original.startswith(b'%PDF-')
    doc=fitz.open(stream=original,filetype='pdf')
    text='\n'.join(page.get_text() for page in doc)
    assert text.count('1. COMPETÊNCIAS TÉCNICAS')==1
    assert text.count('2. COMPETÊNCIAS COMPORTAMENTAIS')==1
    assert text.count('3. PARECER DE RECOMENDAÇÃO')==1
    assert 'Energia Exemplo' in text
    assert 'Transcrição' not in text  # nenhum marcador operacional no documento
    doc.close()
    from PIL import Image
    logo=tmp_path/'cliente.png'
    Image.new('RGB',(300,100),(240,240,240)).save(logo)
    with_logo=render_client_pdf(report, logo_path=logo)
    assert with_logo!=original  # marca do cliente, não a marca estática da plataforma


def test_no_placeholder_or_unsupported_experience():
    report=prepare_report(
      [{'id':'A','category':'hard','criterion':'Novo critério, inserir origem e competência','origin':'','weight':2,'differential':False}],
      {'A':{'text':'Sim'}}, '', '', '', '', 'Auxiliar de Farmácia','Pessoa Fictícia','')
    draft=draft_from_sources(report,'','','','')
    assert 'Novo critério' not in ' '.join(draft['tecnicas']+draft['comportamentais']+[draft['recomendacao']])
    assert report['adherence_percent'] is None


def test_human_review_works_with_career_narrative_after_five_source_capture():
    import tempfile, sys
    from fastapi.testclient import TestClient
    with tempfile.TemporaryDirectory() as temp:
        os.environ['ENTREVISTADOR_ENV']='test'
        os.environ['ENTREVISTADOR_DATA']=temp
        os.environ['ENTREVISTADOR_ADMIN_PASSWORD']='SenhaPrincipal123456789'
        os.environ.pop('ENTREVISTADOR_OLLAMA_MODEL',None)
        sys.modules.pop('server',None)
        import server
        with TestClient(server.APP) as admin, TestClient(server.APP) as candidate:
            assert admin.post('/api/login',data={'identifier':'admin','password':'SenhaPrincipal123456789'}).status_code==200
            v=admin.post('/api/admin/vacancies',data={'title':'Inside Sales','description':'Responsabilidades:\n- Prospectar clientes ativamente.\nHard skills:\n- Registrar leads em CRM.\nSoft skills:\n- Comunicação consultiva.'})
            assert v.status_code==200,v.text
            c=admin.post('/api/admin/candidates',data={
                'vacancy_id':v.json()['id'],'name':'Candidato Fictício',
                'career_narrative_text':'Eu trabalhei na prospecção de contas empresariais. Organizava propostas e acompanhava a negociação comercial com o CRM interno.'},
                files={'cv':('cv.txt',b'Atuou como consultor em atividades de prospeccao de clientes e registro de oportunidades em CRM comercial.','text/plain')})
            assert c.status_code==200,c.text
            cid=c.json()['id'];token=c.json()['invite'].split('/')[-1]
            questions=admin.get('/api/admin/vacancies/'+v.json()['id']).json()['questions']
            for q in questions:
                a=candidate.post(f'/api/invites/{token}/answer',data={
                   'question_id':q['id'],'text':'Eu prospectei clientes e utilizei CRM para registrar contatos, acompanhar propostas e comunicar ao gestor as negociações.'})
                assert a.status_code==200,a.text
            assert candidate.post(f'/api/invites/{token}/complete').status_code==200
            first=questions[0]['id']
            review=admin.post(f'/api/admin/candidates/{cid}/review',json={'decisions':{
                first:{'action':'retificar','score':2,'justification':'Experiência em CRM e prospecção declarada, sem resultado verificável.'}},'comment':'Revisão técnica.'})
            assert review.status_code==200, review.text
            draft=admin.post(f'/api/admin/candidates/{cid}/client-draft')
            assert draft.status_code==200,draft.text[:450]
            assert 'tecnicas' in draft.json()
        sys.modules.pop('server',None)

"""Testes locais de regressão. Execute com: python -m pytest -q"""
import os, sys, json, secrets, tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine import build_questions


def test_roteiro_entrevista_comercial():
    jd='''Responsabilidades:\n- Prospectar clientes ativamente.\n- Conduzir vendas consultivas.\n- Organizar pipeline e registrar etapas no CRM.\nHard skills:\n- Experiência com CRM e prospecção ativa.\nSoft skills:\n- Autonomia, comunicação e resiliência.\nDiferenciais:\n- Venda de cursos.'''
    r=build_questions(jd,limit=18)
    qs=r['questions']
    assert {'responsabilidade','hard','soft'}<=set(q['category'] for q in qs)
    assert any(q['differential'] for q in qs)
    assert any('prospec' in q['question'].lower() for q in qs)
    assert all(q['origin'] and q['expected_evidence'] and q['focus'] for q in qs)
    assert len([q['question'] for q in qs])==len(set(q['question'] for q in qs))


def test_roteiro_financas():
    jd='''Responsabilidades:\n- Controlar contas a pagar e receber.\n- Fazer conciliação bancária.\nHard skills:\n- Excel avançado e ERP.\nSoft skills:\n- Organização, atenção aos detalhes e comunicação.'''
    qs=build_questions(jd,limit=18)['questions']
    assert any('concilia' in q['question'].lower() for q in qs)
    assert any(q['focus']=='Excel aplicado' for q in qs)
    assert any(q['focus']=='Sistemas de gestão' for q in qs)
    assert not any('prospecção' in q['question'].lower() for q in qs)


def test_roteiro_tecnico_software():
    jd='''Responsabilidades:\n- Analisar dados com Python e SQL.\nHard skills:\n- Python, SQL e Power BI.\nSoft skills:\n- Autonomia.'''
    qs=build_questions(jd,limit=18)['questions']
    f={q['focus'] for q in qs}
    assert {'Aplicação prática de Python','Modelagem e consulta SQL','Painéis no Power BI'}<=f


def test_roteiro_nao_inventa_skills():
    qs=build_questions('''Responsabilidades:\n- Fazer conciliação bancária.\nSoft skills:\n- Organização.''')['questions']
    assert not any(q['focus'] in ('Gestão de mídia paga','Prospecção ativa','Modelagem e consulta SQL') for q in qs)


def test_roles_and_question_api():
    from fastapi.testclient import TestClient
    os.environ['ENTREVISTADOR_ENV']='production'
    os.environ['ENTREVISTADOR_PUBLIC_URL']='https://entrevistador-digital.onrender.com'
    os.environ['ENTREVISTADOR_DATA']=tempfile.mkdtemp(prefix='v95pytest_')
    os.environ['ENTREVISTADOR_PRIVACY_CONTACT']='rh@example.org'
    os.environ['ENTREVISTADOR_CONTROLLER_NAME']='Teste'
    pw='A1test'+secrets.token_urlsafe(18)
    os.environ['ENTREVISTADOR_ADMIN_PASSWORD']=pw
    import server
    main=TestClient(server.APP,base_url='https://entrevistador-digital.onrender.com')
    assert main.post('/api/login',data={'identifier':'admin','password':pw}).status_code==200
    user_pw='B1test'+secrets.token_urlsafe(18)
    email='teste@example.org'
    r=main.post('/api/admin/users',json={'name':'Recrutador','email':email,'role':'recrutador','password':user_pw})
    assert r.status_code==201,r.text
    uid=r.json()['id']
    recruiter=TestClient(server.APP,base_url='https://entrevistador-digital.onrender.com')
    assert recruiter.post('/api/login',data={'identifier':email,'password':user_pw}).status_code==200
    assert recruiter.get('/api/admin/users').status_code==403
    assert recruiter.get('/api/admin/vacancies').status_code==403
    assert recruiter.post('/api/admin/me/password',json={'current_password':user_pw,'new_password':'C1new'+secrets.token_urlsafe(18)}).status_code==200
    assert recruiter.get('/api/admin/vacancies').status_code==200
    jd='Responsabilidades:\n- Realizar conciliação bancária.\nHard skills:\n- Excel avançado e ERP.\nSoft skills:\n- Organização e comunicação.'
    r=recruiter.post('/api/admin/vacancies',data={'title':'Financeiro','description':jd})
    assert r.status_code==200,r.text
    vid=r.json()['id']
    assert recruiter.post(f'/api/admin/vacancies/{vid}/regenerate-questions').status_code==200
    qs=recruiter.get(f'/api/admin/vacancies/{vid}').json()['questions']
    assert {'responsabilidade','hard','soft'}<=set(q['category'] for q in qs)
    assert recruiter.put(f'/api/admin/vacancies/{vid}/questions',json={'questions':qs}).status_code==200
    assert main.patch(f'/api/admin/users/{uid}',json={'active':False}).status_code==200
    assert recruiter.get('/api/admin/vacancies').status_code==401

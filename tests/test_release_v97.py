"""Fluxos de implantação do parecer V9.7, sem modelos externos nem dados reais."""
import os,sys,tempfile,io,json,zipfile
from pathlib import Path
from fastapi.testclient import TestClient

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def fresh(temp):
    os.environ['ENTREVISTADOR_ENV']='test'
    os.environ['ENTREVISTADOR_DATA']=temp
    os.environ['ENTREVISTADOR_ADMIN_PASSWORD']='SenhaPrincipal123456789'
    os.environ.pop('ENTREVISTADOR_OLLAMA_MODEL',None)
    sys.modules.pop('server',None)
    import server
    return server


def setup(owner, cand, cv=True):
    desc=('Responsabilidades:\n- Atender clientes e identificar necessidades.\n'
          '- Organizar pedidos e conferir produtos antes da entrega.\n'
          'Hard skills:\n- Experiência com atendimento ao cliente e vendas.\n'
          '- Controle de pedidos e documentos.\n'
          'Soft skills:\n- Comunicação clara e organização.\n'
          '- Resolução de problemas e atenção aos detalhes.')
    v=owner.post('/api/admin/vacancies',data={'title':'Atendente de Farmácia','description':desc})
    assert v.status_code==200,v.text
    vid=v.json()['id']
    kwargs={'data':{'vacancy_id':vid,'name':'Candidato Exemplo','linkedin_url':'https://www.linkedin.com/in/exemplo'},
      'files':{'cv':('curriculo.txt',b'Experiencia em atendimento presencial, controle de pedidos e organizacao de estoque. Atua com clientes e vendas.','text/plain'),
               'disc':('disc.txt',b'Relatorio DISC de exemplo. Dominancia D3, Influencia I4, Estabilidade S6, Conformidade C5.','text/plain')}} if cv else {'data':{'vacancy_id':vid,'name':'Candidato Exemplo'}}
    r=owner.post('/api/admin/candidates',**kwargs)
    assert r.status_code==200,r.text
    cid=r.json()['id'];token=r.json()['invite'].split('/')[-1]
    questions=owner.get(f'/api/admin/vacancies/{vid}').json()['questions']
    assert len(questions)>=3
    return cid,token,questions


def pdf_contains(pdf,words):
    import fitz
    with fitz.open(stream=pdf,filetype='pdf') as d:
        s=' '.join(p.get_text() for p in d)
    for word in words:assert word.lower() in s.lower(),(word,s[:1200])
    return s


def test_full_dossier_is_available_after_completion():
    with tempfile.TemporaryDirectory() as temp:
        server=fresh(temp)
        with TestClient(server.APP) as admin,TestClient(server.APP) as candidate:
            assert admin.post('/api/login',data={'identifier':'admin','password':'SenhaPrincipal123456789'}).status_code==200
            cid,token,qs=setup(admin,candidate)
            for q in qs:
                resp=(f'Na funcao anterior, realizei {q["criterion"]}. '
                      'Organizei as demandas, conferi os registros e acompanhei as entregas ate a conclusao.')
                r=candidate.post(f'/api/invites/{token}/answer',data={'question_id':q['id'],'text':resp})
                assert r.status_code==200,r.text
            finish=candidate.post(f'/api/invites/{token}/complete')
            assert finish.status_code==200,finish.text
            assert finish.json()['dossier_status']=='minuta_disponivel_para_revisao'
            detail=admin.get(f'/api/admin/candidates/{cid}').json()
            report=detail['report'];assert report and report['client_sections']['tecnicas']
            assert report['client_sections']['comportamentais']
            assert report['client_sections']['recomendacao']
            assert report['technical_percent'] is None
            assert report['client_approved_at'] is None
            assert admin.get(f'/api/admin/candidates/{cid}/report.pdf').status_code==409
            prev=admin.get(f'/api/admin/candidates/{cid}/report-preview.pdf')
            assert prev.status_code==200,prev.text[:90] if prev.status_code!=200 else ''
            pdf_contains(prev.content,['COMPETÊNCIAS TÉCNICAS','COMPETÊNCIAS COMPORTAMENTAIS','PARECER DE RECOMENDAÇÃO','MINUTA PARA REVISÃO'])
            sections=report['client_sections']
            r=admin.post(f'/api/admin/candidates/{cid}/client-report',json={'tecnicas':'\n\n'.join(sections['tecnicas']),
                'comportamentais':'\n\n'.join(sections['comportamentais']),
                'recomendacao':sections['recomendacao']+' Revisado pelo recrutador.'})
            assert r.status_code==200,r.text
            bad=admin.post(f'/api/admin/candidates/{cid}/approve-client-report',json={'confirmed':False})
            assert bad.status_code==422
            ok=admin.post(f'/api/admin/candidates/{cid}/approve-client-report',json={'confirmed':True})
            assert ok.status_code==200,ok.text
            final=admin.get(f'/api/admin/candidates/{cid}/report.pdf')
            assert final.status_code==200,final.text[:90] if final.status_code!=200 else ''
            content=pdf_contains(final.content,['COMPETÊNCIAS TÉCNICAS','COMPETÊNCIAS COMPORTAMENTAIS','PARECER DE RECOMENDAÇÃO','Revisado pelo recrutador'])
            assert 'MINUTA PARA REVISÃO' not in content
            assert 'Método de cálculo' not in content
            assert 'Ollama' not in content
            assert 'peso × nota' not in content
            # Editar parecer após aprovação revoga autorização anterior.
            r=admin.post(f'/api/admin/candidates/{cid}/client-report',json={'tecnicas':'Nova análise revista.','comportamentais':'Entrevista revista.','recomendacao':'Nova conclusão.'})
            assert r.status_code==200
            assert admin.get(f'/api/admin/candidates/{cid}/report.pdf').status_code==409
        sys.modules.pop('server',None)


def test_old_audio_does_not_block_documental_dossier():
    with tempfile.TemporaryDirectory() as temp:
        server=fresh(temp)
        with TestClient(server.APP) as admin,TestClient(server.APP) as candidate:
            assert admin.post('/api/login',data={'identifier':'admin','password':'SenhaPrincipal123456789'}).status_code==200
            cid,token,qs=setup(admin,candidate)
            # Os arquivos históricos permanecem. Não inventar texto transcrito.
            with server.conn() as db:
                for q in qs:
                    db.execute('INSERT INTO answers(candidate_id,question_id,mode,text,transcript,audio_file,updated) VALUES(?,?,?,?,?,?,?)',
                               (cid,q['id'],'audio','','',f'audios/{q["id"]}.webm',server.now()))
                db.execute("UPDATE candidates SET status='concluido' WHERE id=?",(cid,))
            start=admin.post(f'/api/admin/candidates/{cid}/analyze',data={'ollama_model':'','auto_transcribe':'false'})
            assert start.status_code==202,start.text
            job=admin.get(f'/api/admin/jobs/{start.json()["job_id"]}').json()
            assert job['status']=='finished'
            r=admin.get(f'/api/admin/candidates/{cid}').json()['report']
            assert r['client_sections']['tecnicas']
            assert any('gravação' in x for x in r['pendencias'])
            assert r['technical_percent'] is None
        sys.modules.pop('server',None)


def test_short_answers_generate_cautious_minuta():
    with tempfile.TemporaryDirectory() as temp:
        server=fresh(temp)
        with TestClient(server.APP) as admin,TestClient(server.APP) as candidate:
            assert admin.post('/api/login',data={'identifier':'admin','password':'SenhaPrincipal123456789'}).status_code==200
            cid,token,qs=setup(admin,candidate,cv=False)
            for q in qs:
                assert candidate.post(f'/api/invites/{token}/answer',data={'question_id':q['id'],'text':'Sim'}).status_code==200
            assert candidate.post(f'/api/invites/{token}/complete').status_code==200
            report=admin.get(f'/api/admin/candidates/{cid}').json()['report']
            assert report['client_sections']['tecnicas']
            assert report['client_sections']['comportamentais']
            assert report['technical_percent'] is None
            assert 'curtas demais' in ' '.join(report['client_sections']['validacoes_tecnicas'])
        sys.modules.pop('server',None)


def test_restore_old_report_draft_preserves_human_reviews():
    with tempfile.TemporaryDirectory() as temp:
        server=fresh(temp)
        with TestClient(server.APP) as admin,TestClient(server.APP) as candidate:
            assert admin.post('/api/login',data={'identifier':'admin','password':'SenhaPrincipal123456789'}).status_code==200
            cid,token,qs=setup(admin,candidate)
            for q in qs:
                assert candidate.post(f'/api/invites/{token}/answer',data={'question_id':q['id'],
                  'text':'Atendi clientes, conferi dados e organizei entregas, relatando os procedimentos usados.'}).status_code==200
            assert candidate.post(f'/api/invites/{token}/complete').status_code==200
            with server.conn() as db:
                r=json.loads(db.execute('SELECT report_json FROM reports WHERE candidate_id=?',(cid,)).fetchone()['report_json'])
                # Simulação de backup legado: o relatório tem histórico de revisão, mas não tem redação externa.
                r.pop('client_sections',None);r['review_history']=[{'id':'Q01','decision':'retificar','human_score':2,'justification':'Evidência examinada'}]
                db.execute('UPDATE reports SET report_json=? WHERE candidate_id=?',(json.dumps(r,ensure_ascii=False),cid))
            restored=admin.post(f'/api/admin/candidates/{cid}/prepare-dossier')
            assert restored.status_code==200,restored.text
            after=admin.get(f'/api/admin/candidates/{cid}').json()['report']
            assert after['review_history']==r['review_history']
            assert after['client_sections']['tecnicas']
            assert after['client_sections']['recomendacao']
        sys.modules.pop('server',None)

import io
import os
import secrets
import sys
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def test_text_only_candidate_flow_and_legacy_audio_kept():
    with tempfile.TemporaryDirectory() as temp:
        os.environ['ENTREVISTADOR_ENV']='test'
        os.environ['ENTREVISTADOR_DATA']=temp
        os.environ['ENTREVISTADOR_ADMIN_PASSWORD']='SenhaPrincipal123456789'
        sys.modules.pop('server',None)
        import server
        with TestClient(server.APP) as owner,TestClient(server.APP) as candidate:
            assert owner.post('/api/login',data={'identifier':'admin','password':'SenhaPrincipal123456789'}).status_code==200
            desc='Responsabilidades:\n- Atendimento comercial.\nHard skills:\n- CRM.\nSoft skills:\n- Comunicação.'
            new=owner.post('/api/admin/vacancies',data={'title':'Vaga Exemplo','description':desc})
            assert new.status_code==200,new.text
            vid=new.json()['id']
            qs=owner.get(f'/api/admin/vacancies/{vid}').json()['questions']
            assert qs
            new=owner.post('/api/admin/candidates',data={'vacancy_id':vid,'name':'Candidato Ficticio'})
            assert new.status_code==200,new.text
            cid=new.json()['id'];token=new.json()['invite'].rsplit('/',1)[-1]
            h=candidate.get(f'/entrevista/{token}')
            assert h.status_code==200
            assert 'id="audioMode"' not in h.text and 'id="startRec"' not in h.text
            assert 'id="answerText"' in h.text
            js=candidate.get('/static/interview.js').text
            assert "MediaRecorder" not in js and 'startRec' not in js
            assert "insertFromPaste" in js
            a=candidate.post(f'/api/invites/{token}/answer',data={'question_id':qs[0]['id'],'text':'Minha resposta de teste.'},files={'audio':('resposta.webm',b'fiction-audio','audio/webm')})
            assert a.status_code==422
            a=candidate.post(f'/api/invites/{token}/answer',data={'question_id':qs[0]['id'],'text':'  Exemplo válido de atuação.  '})
            assert a.status_code==200,a.text
            for q in qs[1:]:
                a=candidate.post(f'/api/invites/{token}/answer',data={'question_id':q['id'],'text':'Relatei tarefas e resultados concretos.'})
                assert a.status_code==200,a.text
            finish=candidate.post(f'/api/invites/{token}/complete')
            assert finish.status_code==200,finish.text
            assert finish.json()['transcription']=='disabled_for_new_answers'
            info=owner.get(f'/api/admin/candidates/{cid}').json()
            assert info['status']=='concluido'
            assert all(a['mode']=='text' and not a['audio_file'] for a in info['answers'].values())
            assert not info['transcription_job']
            # Uma gravação anterior continua vinculada e não pode ser apagada
            # silenciosamente por uma resposta nova de texto.
            with server.conn() as db:
                qid=qs[0]['id']
                db.execute("UPDATE candidates SET status='em_andamento' WHERE id=?",(cid,))
                db.execute("UPDATE answers SET mode='audio',audio_file='audios/registro_antigo.webm',text='' WHERE candidate_id=? AND question_id=?",(cid,qid))
            a=candidate.post(f'/api/invites/{token}/answer',data={'question_id':qid,'text':'Outra resposta digitada.'})
            assert a.status_code==409,a.text
            with server.conn() as db:
                row=db.execute('SELECT audio_file FROM answers WHERE candidate_id=? AND question_id=?',(cid,qid)).fetchone()
                assert row['audio_file']=='audios/registro_antigo.webm'
        sys.modules.pop('server',None)

"""Testa a atualização do parecer depois de retificação humana, sem perder edição existente."""
import subprocess,sys,textwrap,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class ReviewApiTests(unittest.TestCase):
    def test_review_regenerates_and_preserves_reviewed_document(self):
        code=r'''
import os,sys,tempfile,json
from datetime import datetime
root=sys.argv[1]
sys.path.insert(0,root)
with tempfile.TemporaryDirectory() as d:
 os.environ['ENTREVISTADOR_DATA']=d
 import server
 from fastapi.testclient import TestClient
 from technical_engine import prepare_report
 test=TestClient(server.APP)
 login=test.post('/api/login',data={'identifier':'admin','password':server.ADMIN_PASS})
 assert login.status_code==200,login.text
 cid='test_candidate';vid='test_vacancy'
 questions=[
  {'id':'Q01','category':'responsabilidade','criterion':'Atendimento ao público e registro de pedidos','origin':'Atender clientes','weight':3},
  {'id':'Q02','category':'soft','criterion':'Organização e comunicação','origin':'Comunicação e organização','weight':2},
 ]
 answers={'Q01':{'mode':'texto','text':'Atendi diretamente clientes, registrei pedidos e acompanhei as entregas.'},
          'Q02':{'mode':'texto','text':'Organizei a fila de solicitações, comuniquei prazos e expliquei atrasos aos clientes.'}}
 cv='Experiência anterior em atendimento ao público, registro de pedidos e suporte a clientes durante dois anos.'
 disc='DISC: Estabilidade elevada, Conformidade alta.'
 report=prepare_report(questions,answers,cv,disc,'','','Auxiliar de Farmácia','Candidato Fictício','Vaga simulada')
 with server.conn() as db:
  db.execute('INSERT INTO vacancies(id,title,description,questions_json,created) VALUES(?,?,?,?,?)',(vid,'Auxiliar de Farmácia','Vaga simulada',json.dumps(questions),server.now()))
  db.execute('INSERT INTO candidates(id,vacancy_id,name,cv_text,disc_text,token,status,created) VALUES(?,?,?,?,?,?,?,?)',(cid,vid,'Candidato Fictício',cv,disc,'test-token','concluido',server.now()))
  db.execute('INSERT INTO reports(candidate_id,report_json,generated) VALUES(?,?,?)',(cid,json.dumps(report,ensure_ascii=False),server.now()))
 p=test.post('/api/admin/candidates/'+cid+'/review',json={'decisions':{
  'Q01':{'action':'retificar','score':3,'justification':'Atendimento descrito com responsabilidade direta.'},
  'Q02':{'action':'retificar','score':3,'justification':'Organização e comunicação descritas em situação real.'}}})
 assert p.status_code==200,p.text
 data=p.json()
 assert data['draft_source_audit']['criterios_revisados']==2,data['draft_source_audit']
 assert 'atendimento' in ' '.join(data['client_sections']['tecnicas']).lower()
 assert 'DISC' in ' '.join(data['client_sections']['comportamentais'])
 # Simular texto editado, depois alteração de nota: preserva texto e cancela aprovação.
 p=test.post('/api/admin/candidates/'+cid+'/client-report',json={
  'tecnicas':'Experiência profissional em atendimento e registro de pedidos, conforme dados disponíveis.',
  'comportamentais':'Relata organização, comunicação com clientes e acompanhamento de demandas.',
  'recomendacao':'Revisão do recrutador pendente.'})
 assert p.status_code==200,p.text
 p=test.post('/api/admin/candidates/'+cid+'/review',json={'decisions':{
  'Q01':{'action':'retificar','score':2,'justification':'As evidências mostram atendimento, mas não detalham resultados.'}}})
 assert p.status_code==200,p.text
 r=p.json()
 assert r['client_requires_revalidation'] is True
 assert r['client_sections']['tecnicas'][0].startswith('Experiência profissional')
 blocked=test.post('/api/admin/candidates/'+cid+'/approve-client-report',json={'confirmed':True})
 assert blocked.status_code==409,blocked.text
 print('HTTP review flow OK')
'''
        proc=subprocess.run([sys.executable,'-c',code,str(ROOT)],capture_output=True,text=True,timeout=35)
        self.assertEqual(proc.returncode,0,proc.stdout+'\n'+proc.stderr)

if __name__=='__main__':unittest.main()

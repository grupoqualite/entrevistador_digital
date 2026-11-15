"""Regressão para permissões e conteúdo do ZIP. Executar localmente: python -m pytest tests/test_backup_restore.py -q"""
import os, sys, importlib, tempfile, io, zipfile, sqlite3
from pathlib import Path
from fastapi.testclient import TestClient

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def test_restore_rbac_integrity_and_admin_sessions():
    with tempfile.TemporaryDirectory() as td:
        os.environ['ENTREVISTADOR_ENV']='test'
        os.environ['ENTREVISTADOR_DATA']=td
        os.environ['ENTREVISTADOR_ADMIN_PASSWORD']='SenhaTesteAdmin123456789'
        if 'server' in sys.modules:del sys.modules['server']
        import server
        with TestClient(server.APP) as owner,TestClient(server.APP) as secondary,TestClient(server.APP) as recruiter:
            def login(client,user,password):
                r=client.post('/api/login',data={'identifier':user,'password':password})
                assert r.status_code==200,r.text
            login(owner,'admin','SenhaTesteAdmin123456789')
            def create(name,email,role):
                r=owner.post('/api/admin/users',json={'name':name,'email':email,'role':role,'password':'SenhaSegura123456789'})
                assert r.status_code==201,r.text
                return r.json()['id']
            create('Ana Administração','ana@exemplo.com','administrador')
            create('Rui Recrutamento','rui@exemplo.com','recrutador')
            login(secondary,'ana@exemplo.com','SenhaSegura123456789')
            login(recruiter,'rui@exemplo.com','SenhaSegura123456789')
            # Senhas provisórias precisam ser trocadas antes de usar operações administrativas.
            for c in [secondary,recruiter]:
                r=c.post('/api/admin/me/password',json={'current_password':'SenhaSegura123456789','new_password':'SenhaDefinitiva123456789'})
                assert r.status_code==200,r.text
            # Backup e restauração são proibidos para recrutadores.
            assert recruiter.get('/api/admin/backup.zip').status_code==403
            assert recruiter.post('/api/admin/backup/restore',files={'file':('backup.zip',b'arquivo invalido','application/zip')},data={'confirmation':'RESTAURAR BACKUP'}).status_code==403
            with server.conn() as db:
                db.execute('INSERT INTO vacancies(id,title,description,questions_json,warnings_json,created) VALUES(?,?,?,?,?,?)',('a1','Vaga antes','Descrição teste','[]','[]',server.now()))
            # Áudio e documento fictícios devem voltar junto com o SQLite.
            media=server.UPLOADS/'audios'/'fakecandidate'
            media.mkdir(parents=True,exist_ok=True)
            audio=media/'Q01_falso.webm';audio.write_bytes(b'FAKE AUDIO TEST CONTENT')
            with server.conn() as db:
                db.execute('INSERT INTO candidates(id,vacancy_id,name,token,status,created) VALUES(?,?,?,?,?,?)',('fakecandidate','a1','Candidato fictício','TOKENFICTICIO','concluido',server.now()))
                db.execute('INSERT INTO answers(candidate_id,question_id,mode,text,transcript,audio_file,updated) VALUES(?,?,?,?,?,?,?)',('fakecandidate','Q01','audio','','','audios/fakecandidate/Q01_falso.webm',server.now()))
            resp=secondary.get('/api/admin/backup.zip')
            assert resp.status_code==200,resp.text[:200]
            data=resp.content
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                assert 'dados.sqlite3' in z.namelist()
            with server.conn() as db:db.execute('INSERT INTO vacancies(id,title,description,questions_json,warnings_json,created) VALUES(?,?,?,?,?,?)',('a2','Vaga temporária','Não deve continuar','[]','[]',server.now()))
            audio.unlink()  # Simula perda da gravação durante uma implantação.
            missing_confirm=secondary.post('/api/admin/backup/restore',files={'file':('backup.zip',data,'application/zip')},data={'confirmation':'SIM'})
            assert missing_confirm.status_code==422
            assert secondary.post('/api/admin/backup/restore',files={'file':('backup.zip',b'not zip','application/zip')},data={'confirmation':'RESTAURAR BACKUP'}).status_code==422
            # ZIP traversal é recusado e não cria arquivos fora do diretório.
            malicious=io.BytesIO()
            with zipfile.ZipFile(malicious,'w') as z:
                z.writestr('../x.txt','não')
                z.writestr('dados.sqlite3',b'a')
            assert secondary.post('/api/admin/backup/restore',files={'file':('backup.zip',malicious.getvalue(),'application/zip')},data={'confirmation':'RESTAURAR BACKUP'}).status_code==422
            # Um administrador secundário efetivamente recupera o snapshot anterior.
            r=secondary.post('/api/admin/backup/restore',files={'file':('backup.zip',data,'application/zip')},data={'confirmation':'RESTAURAR BACKUP'})
            assert r.status_code==200,r.text
            assert r.json()['requires_relogin']
            assert audio.read_bytes()==b'FAKE AUDIO TEST CONTENT'
            assert server.conn is not None
            with server.conn() as db:
                assert db.execute('SELECT count(*) FROM vacancies WHERE id=?',('a1',)).fetchone()[0]==1
                assert db.execute('SELECT count(*) FROM vacancies WHERE id=?',('a2',)).fetchone()[0]==0
                audit=db.execute("SELECT actor FROM staff_audit WHERE action='restore_backup' ORDER BY at DESC LIMIT 1").fetchone()
                assert audit is not None
                assert db.execute('SELECT COUNT(*) FROM admin_sessions').fetchone()[0]==0
            assert owner.get('/api/admin/me').status_code==401
            assert secondary.get('/api/admin/me').status_code==401
            login(owner,'admin','SenhaTesteAdmin123456789')
            assert owner.get('/api/admin/users').status_code==200
        sys.modules.pop('server',None)

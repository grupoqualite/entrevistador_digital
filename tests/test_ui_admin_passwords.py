import sys, os, tempfile, zipfile, io
from pathlib import Path
from fastapi.testclient import TestClient
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def test_admin_backup_ui_and_eight_character_passwords():
    with tempfile.TemporaryDirectory() as temp:
        os.environ['ENTREVISTADOR_ENV']='test'
        os.environ['ENTREVISTADOR_DATA']=temp
        os.environ['ENTREVISTADOR_ADMIN_PASSWORD']='SenhaPrincipal123456789'
        sys.modules.pop('server',None)
        import server
        with TestClient(server.APP) as owner, TestClient(server.APP) as second_admin, TestClient(server.APP) as recruiter:
            assert owner.get('/api/health').json()['version']=='9.7.7-parecer-qualite'
            html=owner.get('/').text
            assert 'id="backupsTab"' in html and 'id="restoreForm"' in html and 'id="openRestore"' in html
            assert 'minlength="8"' in html and 'minlength="16"' not in html
            js=owner.get('/static/app.js').text
            assert "'backupsTab'" in js and "'openRestore'" in js
            assert owner.post('/api/login',data={'identifier':'admin','password':'SenhaPrincipal123456789'}).status_code==200
            assert owner.post('/api/admin/users',json={'name':'Muito curta','email':'short@example.com','role':'recrutador','password':'abc1234'}).status_code==422
            assert owner.post('/api/admin/users',json={'name':'Sem dígitos','email':'nodigit@example.com','role':'recrutador','password':'abcdefgh'}).status_code==422
            a=owner.post('/api/admin/users',json={'name':'Ana Admin','email':'ana@example.com','role':'administrador','password':'abcde123'})
            assert a.status_code==201, a.text
            b=owner.post('/api/admin/users',json={'name':'Rui Recrutador','email':'rui@example.com','role':'recrutador','password':'abcde123'})
            assert b.status_code==201,b.text
            assert second_admin.post('/api/login',data={'identifier':'ana@example.com','password':'abcde123'}).status_code==200
            assert recruiter.post('/api/login',data={'identifier':'rui@example.com','password':'abcde123'}).status_code==200
            assert second_admin.post('/api/admin/me/password',json={'current_password':'abcde123','new_password':'mudar123'}).status_code==200
            assert recruiter.post('/api/admin/me/password',json={'current_password':'abcde123','new_password':'mudar123'}).status_code==200
            assert owner.post('/api/admin/users/'+a.json()['id']+'/reset-password',json={'new_password':'senha123'}).status_code==200
            assert recruiter.get('/api/admin/backup.zip').status_code==403
            assert recruiter.post('/api/admin/backup/restore',files={'file':('backup.zip',b'bad','application/zip')},data={'confirmation':'RESTAURAR BACKUP'}).status_code==403
            assert owner.get('/api/admin/backup.zip').status_code==200
            # After password reset, old admin session may be invalidated, so test new password.
            assert second_admin.post('/api/login',data={'identifier':'ana@example.com','password':'senha123'}).status_code==200
            assert second_admin.post('/api/admin/me/password',json={'current_password':'senha123','new_password':'outra123'}).status_code==200
            assert second_admin.get('/api/admin/backup.zip').status_code==200
        sys.modules.pop('server',None)

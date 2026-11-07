"""Entrevistador Digital V7: matriz técnica por evidências, áudio e homologação humana."""
from __future__ import annotations
import os, json, sqlite3, secrets, hashlib, time, re, io, html
from pathlib import Path
from datetime import datetime, timedelta
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException, Response
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, StreamingResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import cm
from extractors import extract, MAX_UPLOAD
from engine import build_questions
from technical_engine import prepare_report, update_review, metrics, RUBRIC
from evaluator_v9 import evaluate_v9
from draft_v9 import draft_sections
from evidence_draft import draft_from_sources
from question_upgrade_v9 import improve_questions
from client_report import render_client_pdf

BASE=Path(__file__).resolve().parent
PRODUCTION=os.environ.get('ENTREVISTADOR_ENV','').lower()=='production'
if PRODUCTION:
    required=['ENTREVISTADOR_ADMIN_PASSWORD','ENTREVISTADOR_PUBLIC_URL','ENTREVISTADOR_DATA','ENTREVISTADOR_PRIVACY_CONTACT','ENTREVISTADOR_CONTROLLER_NAME']
    missing=[x for x in required if not os.environ.get(x)]
    if missing:raise RuntimeError('Configuração obrigatória de produção ausente: '+', '.join(missing))
    if not os.environ['ENTREVISTADOR_PUBLIC_URL'].startswith('https://'):
        raise RuntimeError('O endereço público da versão de produção deve utilizar HTTPS.')
    if len(os.environ['ENTREVISTADOR_ADMIN_PASSWORD'])<16:
        raise RuntimeError('A senha administrativa de produção deve ter ao menos 16 caracteres.')
DATA=Path(os.environ.get('ENTREVISTADOR_DATA',str(BASE/'dados'))).expanduser().resolve()
UPLOADS=DATA/'arquivos'
DATA.mkdir(parents=True,exist_ok=True);UPLOADS.mkdir(parents=True,exist_ok=True)
try:os.chmod(DATA,0o700);os.chmod(UPLOADS,0o700)
except OSError:pass
DB=DATA/'dados.sqlite3'
ADMIN_KEY_FILE=DATA/'CHAVE_ADMINISTRATIVA.txt'
if os.environ.get('ENTREVISTADOR_ADMIN_PASSWORD'):
    ADMIN_PASS=os.environ['ENTREVISTADOR_ADMIN_PASSWORD']
else:
    if not ADMIN_KEY_FILE.exists():
        password=secrets.token_urlsafe(18)
        ADMIN_KEY_FILE.write_text(password,encoding='utf-8')
        try: os.chmod(ADMIN_KEY_FILE,0o600)
        except OSError:pass
    ADMIN_PASS=ADMIN_KEY_FILE.read_text(encoding='utf-8').strip()
ADMIN_HASH=hashlib.sha256(ADMIN_PASS.encode()).hexdigest()
LOGIN_TRACKER={}
POOL=ThreadPoolExecutor(max_workers=1,thread_name_prefix='edv9-job')
APP=FastAPI(title='Entrevistador Digital V9',version='9.6.1',docs_url=None if PRODUCTION else '/docs',redoc_url=None if PRODUCTION else '/redoc')
APP.mount('/static',StaticFiles(directory=str(BASE/'static')),name='static')

@contextmanager
def conn():
    db=sqlite3.connect(DB,timeout=15);db.row_factory=sqlite3.Row
    db.execute('PRAGMA busy_timeout=15000')
    db.execute('PRAGMA foreign_keys = ON')
    try:
        yield db;db.commit()
    finally:db.close()
with conn() as db:
    db.execute('PRAGMA journal_mode=WAL')
    db.executescript('''
    CREATE TABLE IF NOT EXISTS vacancies(id TEXT PRIMARY KEY,title TEXT NOT NULL,description TEXT NOT NULL,questions_json TEXT NOT NULL,warnings_json TEXT DEFAULT '[]',created TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS candidates(id TEXT PRIMARY KEY,vacancy_id TEXT NOT NULL REFERENCES vacancies(id),name TEXT NOT NULL,linkedin_url TEXT DEFAULT '',cv_text TEXT DEFAULT '',disc_text TEXT DEFAULT '',linkedin_text TEXT DEFAULT '',cv_file TEXT DEFAULT '',disc_file TEXT DEFAULT '',linkedin_file TEXT DEFAULT '',token TEXT NOT NULL UNIQUE,status TEXT NOT NULL DEFAULT 'convidado',created TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS answers(candidate_id TEXT NOT NULL REFERENCES candidates(id),question_id TEXT NOT NULL,mode TEXT NOT NULL,text TEXT DEFAULT '',transcript TEXT DEFAULT '',audio_file TEXT DEFAULT '',updated TEXT NOT NULL,PRIMARY KEY(candidate_id,question_id));
    CREATE TABLE IF NOT EXISTS reports(candidate_id TEXT PRIMARY KEY REFERENCES candidates(id),report_json TEXT NOT NULL,generated TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS admin_sessions(token_hash TEXT PRIMARY KEY,expires_at REAL NOT NULL,created_at REAL NOT NULL);
    CREATE TABLE IF NOT EXISTS staff_users(
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE COLLATE NOCASE,
        role TEXT NOT NULL CHECK(role IN ('administrador','recrutador')),
        password_salt TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        active INTEGER NOT NULL DEFAULT 1,
        must_change_password INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        last_login_at TEXT
    );
    CREATE TABLE IF NOT EXISTS staff_audit(
        id TEXT PRIMARY KEY,
        actor TEXT NOT NULL,
        action TEXT NOT NULL,
        subject_id TEXT,
        at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS analysis_jobs(id TEXT PRIMARY KEY,candidate_id TEXT NOT NULL,status TEXT NOT NULL,progress INTEGER NOT NULL DEFAULT 0,total INTEGER NOT NULL DEFAULT 0,error TEXT DEFAULT '',created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS transcription_jobs(id TEXT PRIMARY KEY,candidate_id TEXT NOT NULL REFERENCES candidates(id),status TEXT NOT NULL,progress INTEGER NOT NULL DEFAULT 0,total INTEGER NOT NULL DEFAULT 0,error TEXT DEFAULT '',created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
    ''')
    sess_cols={r['name'] for r in db.execute('PRAGMA table_info(admin_sessions)').fetchall()}
    if 'user_id' not in sess_cols:
        db.execute("ALTER TABLE admin_sessions ADD COLUMN user_id TEXT NOT NULL DEFAULT '__owner__'")
        # Sessões anteriores à migração não têm identidade individual; exigir novo login.
        db.execute('DELETE FROM admin_sessions')
    existing={r['name'] for r in db.execute('PRAGMA table_info(candidates)').fetchall()}
    if 'invite_expires_at' not in existing:db.execute('ALTER TABLE candidates ADD COLUMN invite_expires_at TEXT')
    if 'revoked_at' not in existing:db.execute('ALTER TABLE candidates ADD COLUMN revoked_at TEXT')
    db.execute("UPDATE analysis_jobs SET status='failed',error='Análise interrompida por reinicialização; execute novamente.' WHERE status IN ('queued','running')")
    db.execute("UPDATE transcription_jobs SET status='interrompido',error='Servidor reiniciado durante a transcrição. Reprocesse os áudios.' WHERE status IN ('queued','running')")
    if not PRODUCTION and not db.execute('SELECT 1 FROM vacancies LIMIT 1').fetchone():
        sample='''EXECUTIVO(A) DE VENDAS | AWEN ESPAÇO INTEGRATIVO
Local: Campinas, São José/SC | Presencial | PJ
Responsabilidades:
- Prospectar ativamente novos clientes e gerar oportunidades comerciais.
- Conduzir atendimentos e vendas consultivas de forma presencial e por canais digitais.
- Qualificar leads, compreender necessidades e orientar o cliente sobre formações profissionais.
- Negociar propostas comerciais e contornar objeções até o fechamento.
- Organizar pipeline, registrar atividades no CRM e realizar follow-ups.
- Acompanhar metas e indicadores de conversão e apresentar resultados.
Hard skills:
- Experiência com prospecção ativa e negociação comercial.
- Prática em CRM e gestão de funil de vendas.
Soft skills:
- Autonomia, iniciativa, resiliência e escuta ativa.
- Comunicação clara e orientação a resultados.
Diferenciais:
- Experiência com vendas de cursos, educação profissional ou pós-graduação.
'''
        result=build_questions(sample,'',15)
        db.execute('INSERT INTO vacancies VALUES(?,?,?,?,?,?)',('vagademo','Executivo(a) de Vendas | Awen',sample,json.dumps(result['questions'],ensure_ascii=False),json.dumps(result['warnings'],ensure_ascii=False),datetime.now().isoformat()))

def now():return datetime.now().isoformat(timespec='seconds')
def uid():return secrets.token_hex(8)
def fmt_row(r):return dict(r) if r else None

def password_hash(password:str,salt_hex:str)->str:
    # PBKDF2 com sal único por usuário. O valor da senha jamais é armazenado.
    return hashlib.pbkdf2_hmac('sha256',password.encode('utf-8'),bytes.fromhex(salt_hex),600_000).hex()

def validate_password(password:str):
    if len(password)<16 or len(password)>256:
        raise HTTPException(422,'A senha precisa ter entre 16 e 256 caracteres.')
    if not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
        raise HTTPException(422,'A senha precisa conter letras e números.')

def current_actor(request:Request):
    token=request.cookies.get('ed_sess','')
    if len(token)<28:return None
    with conn() as db:
        row=db.execute('SELECT user_id,expires_at FROM admin_sessions WHERE token_hash=?',(hashlib.sha256(token.encode()).hexdigest(),)).fetchone()
        if not row or row['expires_at']<=time.time():return None
        if row['user_id']=='__owner__':
            return {'id':'__owner__','name':'Administrador principal','email':'admin','role':'administrador','owner':True,'must_change_password':False}
        u=db.execute('SELECT id,name,email,role,active,must_change_password FROM staff_users WHERE id=?',(row['user_id'],)).fetchone()
        if not u or not u['active']:return None
        actor=dict(u);actor['owner']=False;actor['must_change_password']=bool(actor['must_change_password'])
        return actor

def authorized(request:Request)->bool:
    return current_actor(request) is not None

def must_admin(request:Request):
    actor=current_actor(request)
    if not actor:raise HTTPException(status_code=401,detail='Faça login para acessar o painel.')
    if actor['must_change_password']:
        raise HTTPException(status_code=403,detail='Altere sua senha provisória antes de acessar o painel.')
    return actor

def must_manage_users(request:Request):
    actor=must_admin(request)
    if actor['role']!='administrador':raise HTTPException(403,'Somente administradores podem gerenciar usuários.')
    return actor

def public_actor(actor:dict)->dict:
    return {k:actor[k] for k in ('id','name','email','role','owner','must_change_password')}

def record_audit(db,actor,action,subject_id=None):
    db.execute('INSERT INTO staff_audit(id,actor,action,subject_id,at) VALUES(?,?,?,?,?)',
               (secrets.token_hex(12),actor['id'],action,subject_id,now()))


def get_candidate(token:str):
    with conn() as db:
        c=db.execute('SELECT * FROM candidates WHERE token=?',(token,)).fetchone()
        if not c:raise HTTPException(404,'Convite não encontrado.')
        if c['revoked_at']:raise HTTPException(410,'Convite cancelado.')
        if c['invite_expires_at'] and c['invite_expires_at']<now():raise HTTPException(410,'Convite expirado. Solicite um novo link ao recrutador.')
        return dict(c)

def get_vacancy(v_id:str):
    with conn() as db:
        v=db.execute('SELECT * FROM vacancies WHERE id=?',(v_id,)).fetchone()
        if not v:raise HTTPException(404,'Vaga não encontrada.')
        return dict(v)

def get_answers(cid:str):
    with conn() as db:
        return {r['question_id']:dict(r) for r in db.execute('SELECT * FROM answers WHERE candidate_id=?',(cid,)).fetchall()}

async def save_file(file:UploadFile|None,subdir:str)->tuple[str,str,dict]:
    if not file or not file.filename:return '','',{}
    content=await file.read(MAX_UPLOAD+1)
    if len(content)>MAX_UPLOAD:raise HTTPException(413,'Arquivo acima de 12 MB.')
    try: ex=extract(file.filename,content)
    except Exception as err:raise HTTPException(422,f'{file.filename}: {err}')
    suffix=Path(file.filename).suffix.lower()
    stored=f'{subdir}/{secrets.token_hex(14)}{suffix}'
    directory=UPLOADS/subdir;directory.mkdir(parents=True,exist_ok=True)
    (UPLOADS/stored).write_bytes(content)
    return stored,ex['text'],ex

@APP.get('/',response_class=HTMLResponse)
async def home():return FileResponse(BASE/'static/index.html')
@APP.get('/entrevista/{token}',response_class=HTMLResponse)
async def interview_screen(token:str):
    get_candidate(token)
    return FileResponse(BASE/'static/interview.html')

@APP.get('/privacidade',response_class=HTMLResponse)
def privacy_notice():
    controller=html.escape(os.environ.get('ENTREVISTADOR_CONTROLLER_NAME','Responsável pelo processo seletivo'))
    contact=html.escape(os.environ.get('ENTREVISTADOR_PRIVACY_CONTACT','Informe o canal de privacidade ao recrutador'))
    retention=html.escape(os.environ.get('ENTREVISTADOR_RETENTION_DAYS','90'))
    return HTMLResponse(f"""<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
    <title>Informações de privacidade</title><style>body{{font:16px/1.65 system-ui;margin:2em auto;padding:0 20px;max-width:760px;color:#172f48}}h1{{font-size:1.5em}}</style></head>
    <body><h1>Informações sobre os dados da entrevista</h1>
    <p><strong>Responsável informado:</strong> {controller}. <strong>Contato:</strong> {contact}.</p>
    <p>Os dados de currículo, experiências profissionais, respostas escritas, áudios e avaliações de competências são tratados para apoiar a análise da candidatura à vaga indicada. O relatório DISC, quando fornecido, é considerado como informação complementar e não determina automaticamente a decisão.</p>
    <p>O sistema pode produzir uma avaliação preliminar por processamento automatizado. A decisão sobre a candidatura é de responsabilidade do recrutador, que deverá revisar as evidências e o parecer.</p>
    <p>O acesso aos registros é limitado aos responsáveis autorizados pelo processo seletivo. O prazo previsto para reavaliação da necessidade de guarda é de {retention} dias, sujeito à política aplicável do controlador.</p>
    <p>Você pode solicitar informações, correção ou exclusão de dados, conforme aplicável, pelo canal informado acima. A base legal do tratamento deve ser definida e comunicada pelo controlador conforme a situação concreta.</p>
    <p>Para perguntas sobre o uso dos seus dados, procure o responsável pelo processo seletivo.</p>
    </body></html>""")

BRANDING_DIR=DATA/'branding'
LOGO_PATH=BRANDING_DIR/'logo.png'

@APP.get('/api/brand/logo')
def company_logo():
    if not LOGO_PATH.is_file():raise HTTPException(404,'Logotipo não configurado.')
    return FileResponse(LOGO_PATH,media_type='image/png',headers={'Cache-Control':'no-store'})

@APP.post('/api/admin/brand/logo')
async def upload_company_logo(request:Request,file:UploadFile=File(...)):
    must_admin(request)
    if Path(file.filename or '').suffix.lower() not in ('.png','.jpg','.jpeg'):
        raise HTTPException(415,'Envie logotipo em PNG ou JPG. SVG não está habilitado neste piloto.')
    data=await file.read(3*1024*1024+1)
    if not data or len(data)>3*1024*1024:
        raise HTTPException(413,'Imagem vazia ou maior que 3 MB.')
    from PIL import Image,UnidentifiedImageError
    try:
        image=Image.open(io.BytesIO(data))
        if image.format not in ('PNG','JPEG') or image.width*image.height>8_000_000:
            raise ValueError('Formato ou dimensões inválidas.')
        image.load()
        if image.mode not in ('RGB','RGBA'):image=image.convert('RGBA')
    except (UnidentifiedImageError,ValueError,OSError) as e:
        raise HTTPException(422,'Imagem inválida: '+str(e)[:120])
    BRANDING_DIR.mkdir(parents=True,exist_ok=True)
    temp=BRANDING_DIR/('logo-'+secrets.token_hex(4)+'.png')
    image.save(temp,format='PNG',optimize=True)
    os.replace(temp,LOGO_PATH)
    return {'ok':True,'logo_url':'/api/brand/logo'}

@APP.delete('/api/admin/brand/logo')
def remove_company_logo(request:Request):
    must_admin(request)
    LOGO_PATH.unlink(missing_ok=True)
    return {'ok':True}

@APP.get('/api/health')
def health():return {'ok':True,'version':'9.6.1-evidence-draft','storage':'EFEMERO - dados perdidos em reinicializacoes/hibernacao', 'transcription':'faster-whisper TINY cpu pt-BR (experimental; confirme logs e precisao)','analysis':'manual - sem Ollama neste plano','pilot_only':True}

@APP.post('/api/login')
async def login(request:Request,response:Response,password:str=Form(...),identifier:str=Form('')):
    # Compatibilidade: login principal com apenas a antiga chave administrativa.
    identifier=identifier.strip().lower()
    ip=request.client.host if request.client else 'unknown'
    tracker_key=ip+':'+identifier[:100]
    period=time.time();track=[x for x in LOGIN_TRACKER.get(tracker_key,[]) if x>period-900]
    if len(track)>=8:raise HTTPException(429,'Muitas tentativas. Aguarde 15 minutos.')
    user_id=None
    if identifier in ('','admin','administrador'):
        match=secrets.compare_digest(hashlib.sha256(password.encode()).hexdigest(),ADMIN_HASH)
        if match:user_id='__owner__'
    else:
        match=False
        with conn() as db:
            user=db.execute('SELECT * FROM staff_users WHERE email=? COLLATE NOCASE',(identifier,)).fetchone()
        if user and user['active']:
            supplied=password_hash(password,user['password_salt'])
            match=secrets.compare_digest(supplied,user['password_hash'])
            if match:user_id=user['id']
    if not user_id:
        LOGIN_TRACKER[tracker_key]=track+[period]
        raise HTTPException(401,'Usuário ou senha incorretos.')
    LOGIN_TRACKER.pop(tracker_key,None)
    token=secrets.token_urlsafe(40)
    with conn() as db:
        db.execute('DELETE FROM admin_sessions WHERE expires_at<?',(period,))
        db.execute('INSERT INTO admin_sessions(token_hash,expires_at,created_at,user_id) VALUES(?,?,?,?)',
                   (hashlib.sha256(token.encode()).hexdigest(),period+8*3600,period,user_id))
        if user_id!='__owner__':
            db.execute('UPDATE staff_users SET last_login_at=? WHERE id=?',(now(),user_id))
    response.set_cookie('ed_sess',token,max_age=8*3600,httponly=True,samesite='strict',secure=PRODUCTION or bool(os.environ.get('ENTREVISTADOR_SECURE_COOKIE')=='1'),path='/')
    return {'ok':True,'must_change_password':bool(user_id!='__owner__' and user['must_change_password'])}

@APP.post('/api/logout')
def logout(request:Request,response:Response):
    token=request.cookies.get('ed_sess','')
    if token:
        with conn() as db:db.execute('DELETE FROM admin_sessions WHERE token_hash=?',(hashlib.sha256(token.encode()).hexdigest(),))
    response.delete_cookie('ed_sess',path='/')
    return {'ok':True}

@APP.get('/api/admin/me')
def me(request:Request):
    actor=current_actor(request)
    if not actor:raise HTTPException(401,'Faça login para acessar o painel.')
    return {'ok':True,**public_actor(actor)}

@APP.post('/api/admin/me/password')
async def change_own_password(request:Request):
    actor=current_actor(request)
    if not actor:raise HTTPException(401,'Faça login primeiro.')
    if actor['owner']:
        raise HTTPException(403,'A senha do administrador principal é alterada em Environment no Render.')
    body=await request.json()
    old=str(body.get('current_password') or '')
    new=str(body.get('new_password') or '')
    validate_password(new)
    with conn() as db:
        u=db.execute('SELECT * FROM staff_users WHERE id=?',(actor['id'],)).fetchone()
        if not u or not u['active']:raise HTTPException(401,'Conta desativada.')
        if not secrets.compare_digest(password_hash(old,u['password_salt']),u['password_hash']):
            raise HTTPException(401,'Senha atual incorreta.')
        if secrets.compare_digest(password_hash(new,u['password_salt']),u['password_hash']):
            raise HTTPException(422,'A nova senha precisa ser diferente da anterior.')
        salt=secrets.token_hex(16)
        db.execute('UPDATE staff_users SET password_salt=?,password_hash=?,must_change_password=0,updated_at=? WHERE id=?',
                   (salt,password_hash(new,salt),now(),actor['id']))
        record_audit(db,actor,'change_own_password',actor['id'])
    return {'ok':True}

@APP.get('/api/admin/users')
def list_staff_users(request:Request):
    must_manage_users(request)
    with conn() as db:
        return [dict(r) for r in db.execute('''SELECT id,name,email,role,active,must_change_password,created_at,last_login_at
                     FROM staff_users ORDER BY created_at DESC''').fetchall()]

@APP.post('/api/admin/users',status_code=201)
async def create_staff_user(request:Request):
    actor=must_manage_users(request)
    body=await request.json()
    name=str(body.get('name') or '').strip()
    email=str(body.get('email') or '').strip().lower()
    role=str(body.get('role') or '')
    password=str(body.get('password') or '')
    if not (2<=len(name)<=120):raise HTTPException(422,'Informe um nome de 2 a 120 caracteres.')
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email) or len(email)>254:
        raise HTTPException(422,'Informe um e-mail válido.')
    if role not in ('administrador','recrutador'):raise HTTPException(422,'Perfil inválido.')
    validate_password(password)
    salt=secrets.token_hex(16);user_id=uid()
    with conn() as db:
        try:
            db.execute('''INSERT INTO staff_users(id,name,email,role,password_salt,password_hash,active,must_change_password,created_at,updated_at)
                          VALUES(?,?,?,?,?,?,1,1,?,?)''',
                       (user_id,name,email,role,salt,password_hash(password,salt),now(),now()))
        except sqlite3.IntegrityError:raise HTTPException(409,'Já existe um usuário com esse e-mail.')
        record_audit(db,actor,'create_user',user_id)
    return {'ok':True,'id':user_id,'email':email,'role':role,'must_change_password':True}

@APP.patch('/api/admin/users/{user_id}')
async def update_staff_user(request:Request,user_id:str):
    actor=must_manage_users(request)
    body=await request.json()
    allowed={'name','role','active'}
    if not body or set(body)-allowed:raise HTTPException(422,'Envie apenas nome, perfil ou situação.')
    with conn() as db:
        existing=db.execute('SELECT * FROM staff_users WHERE id=?',(user_id,)).fetchone()
        if not existing:raise HTTPException(404,'Usuário não encontrado.')
        name=str(body.get('name',existing['name'])).strip()
        role=str(body.get('role',existing['role']))
        active=body.get('active',bool(existing['active']))
        if not (2<=len(name)<=120) or role not in ('administrador','recrutador') or not isinstance(active,bool):
            raise HTTPException(422,'Dados inválidos.')
        db.execute('UPDATE staff_users SET name=?,role=?,active=?,updated_at=? WHERE id=?',(name,role,int(active),now(),user_id))
        if not active or role!=existing['role']:
            db.execute('DELETE FROM admin_sessions WHERE user_id=?',(user_id,))
        record_audit(db,actor,'update_user',user_id)
    return {'ok':True}

@APP.post('/api/admin/users/{user_id}/reset-password')
async def reset_staff_password(request:Request,user_id:str):
    actor=must_manage_users(request)
    body=await request.json()
    password=str(body.get('new_password') or '')
    validate_password(password)
    salt=secrets.token_hex(16)
    with conn() as db:
        u=db.execute('SELECT id FROM staff_users WHERE id=?',(user_id,)).fetchone()
        if not u:raise HTTPException(404,'Usuário não encontrado.')
        db.execute('UPDATE staff_users SET password_salt=?,password_hash=?,must_change_password=1,updated_at=? WHERE id=?',
                   (salt,password_hash(password,salt),now(),user_id))
        db.execute('DELETE FROM admin_sessions WHERE user_id=?',(user_id,))
        record_audit(db,actor,'reset_password',user_id)
    return {'ok':True,'must_change_password':True}

@APP.post('/api/admin/extract')
async def preview(request:Request,file:UploadFile=File(...)):
    must_admin(request)
    data=await file.read(MAX_UPLOAD+1)
    if len(data)>MAX_UPLOAD:raise HTTPException(413,'Arquivo acima do limite.')
    try:r=extract(file.filename,data)
    except Exception as e:raise HTTPException(422,str(e))
    return r

@APP.get('/api/admin/vacancies')
def vacancies(request:Request):
    must_admin(request)
    with conn() as db:
        rows=db.execute('SELECT id,title,created FROM vacancies ORDER BY created DESC').fetchall()
        return [dict(r) for r in rows]

@APP.post('/api/admin/vacancies')
async def create_vacancy(request:Request,title:str=Form(...),description:str=Form(...)):
    must_admin(request)
    title=title.strip()[:160];description=description.strip()[:120000]
    if not title or len(description)<35:raise HTTPException(422,'Informe o cargo e a descrição da vaga (mínimo de 35 caracteres).')
    built=build_questions(description,'',18)
    v_id=uid()
    with conn() as db:
        db.execute('INSERT INTO vacancies VALUES(?,?,?,?,?,?)',(v_id,title,description,json.dumps(built['questions'],ensure_ascii=False),json.dumps(built['warnings'],ensure_ascii=False),now()))
    return {'id':v_id,'generated':len(built['questions']),'warnings':built['warnings']}

@APP.get('/api/admin/vacancies/{v_id}')
def vacancy_detail(request:Request,v_id:str):
    must_admin(request)
    v=get_vacancy(v_id)
    return {'id':v['id'],'title':v['title'],'description':v['description'],'questions':json.loads(v['questions_json']),'warnings':json.loads(v['warnings_json'])}

@APP.put('/api/admin/vacancies/{v_id}/questions')
async def update_questions(request:Request,v_id:str):
    must_admin(request);get_vacancy(v_id)
    with conn() as db:
        if db.execute('SELECT 1 FROM candidates WHERE vacancy_id=? LIMIT 1',(v_id,)).fetchone():
            raise HTTPException(409,'Esta vaga já possui convites. Para alterar o questionário, crie uma nova versão da vaga, preservando as entrevistas existentes.')
    body=await request.json(); qs=body.get('questions',[])
    if not isinstance(qs,list) or len(qs)>40:raise HTTPException(422,'Lista inválida, máximo de 40 perguntas.')
    cleans=[]
    for i,q in enumerate(qs,1):
        if not isinstance(q,dict):continue
        question=str(q.get('question','')).strip()[:1200]
        if len(question)<12:continue
        label=str(q.get('category','hard'))
        if label not in ('responsabilidade','hard','soft','logistica'):label='hard'
        cleans.append({'id':f'Q{i:02d}','category':label,'category_label':{'responsabilidade':'Responsabilidades','hard':'Hard skills','soft':'Soft skills','logistica':'Condições da vaga'}[label], 'criterion':str(q.get('criterion',''))[:250], 'origin':str(q.get('origin',''))[:500], 'line':q.get('line',0), 'differential':bool(q.get('differential',False)),'weight':max(1,min(5,int(q.get('weight',2)))),'question':question,'focus':str(q.get('focus',''))[:140], 'expected_evidence':str(q.get('expected_evidence',''))[:350], 'cv_observation':''})
    if not cleans:raise HTTPException(422,'Mantenha ao menos uma pergunta válida.')
    with conn() as db:
        db.execute('UPDATE vacancies SET questions_json=? WHERE id=?',(json.dumps(cleans,ensure_ascii=False),v_id))
    return {'ok':True,'questions':cleans}

@APP.post('/api/admin/vacancies/{v_id}/regenerate-questions')
async def regenerate_vacancy_questions(request:Request,v_id:str):
    must_admin(request)
    v=get_vacancy(v_id)
    with conn() as db:
        if db.execute('SELECT 1 FROM candidates WHERE vacancy_id=? LIMIT 1',(v_id,)).fetchone():
            raise HTTPException(409,'A vaga já possui convites. Crie uma nova vaga para não alterar entrevistas iniciadas.')
    result=build_questions(v['description'],'',18)
    if not result['questions']:
        raise HTTPException(422,'Não foi possível encontrar requisitos na descrição. Revise o texto importado.')
    with conn() as db:
        db.execute('UPDATE vacancies SET questions_json=?,warnings_json=? WHERE id=?',
            (json.dumps(result['questions'],ensure_ascii=False),json.dumps(result['warnings'],ensure_ascii=False),v_id))
    return {'ok':True,'questions':result['questions'],'warnings':result['warnings'],'generated':len(result['questions']),'engine':result['engine']}

@APP.post('/api/admin/vacancies/{v_id}/improve-questions')
async def improve_vacancy_questions(request:Request,v_id:str):
    must_admin(request)
    v=get_vacancy(v_id)
    with conn() as db:
        if db.execute('SELECT 1 FROM candidates WHERE vacancy_id=? LIMIT 1',(v_id,)).fetchone():
            raise HTTPException(409,'Já existem convites desta vaga. Crie uma nova versão antes de alterar as perguntas.')
    model=os.environ.get('ENTREVISTADOR_OLLAMA_MODEL','').strip()
    if not model:raise HTTPException(503,'Modelo local não configurado.')
    try:
        updated,count=await run_in_threadpool(improve_questions,v['description'],json.loads(v['questions_json']),model,
                            os.environ.get('ENTREVISTADOR_OLLAMA_URL','http://127.0.0.1:11434'))
    except Exception as ex:raise HTTPException(503,'Não foi possível aprimorar o roteiro: '+str(ex)[:180])
    with conn() as db:
        db.execute('UPDATE vacancies SET questions_json=? WHERE id=?',(json.dumps(updated,ensure_ascii=False),v_id))
    return {'ok':True,'aprimoradas':count,'questions':updated}

@APP.get('/api/admin/candidates')
def candidate_list(request:Request):
    must_admin(request)
    with conn() as db:
        return [dict(r) for r in db.execute('SELECT c.id,c.name,c.status,c.created,c.token,v.title AS vacancy FROM candidates c JOIN vacancies v ON v.id=c.vacancy_id ORDER BY c.created DESC').fetchall()]

@APP.post('/api/admin/candidates')
async def create_candidate(request:Request,vacancy_id:str=Form(...),name:str=Form(...),linkedin_url:str=Form(''),linkedin_text:str=Form(''),cv:Optional[UploadFile]=File(None),disc:Optional[UploadFile]=File(None),linkedin_pdf:Optional[UploadFile]=File(None),disc_comparativo:Optional[UploadFile]=File(None)):
    must_admin(request);get_vacancy(vacancy_id)
    name=name.strip()[:150]
    if not name:raise HTTPException(422,'Informe um nome.')
    if linkedin_url and not re.match(r'^https://(www\.)?linkedin\.com/(in|pub)/',linkedin_url,re.I):raise HTTPException(422,'Informe um link HTTPS de perfil LinkedIn válido ou deixe em branco.')
    cid=uid();folder=f'candidatos/{cid}'
    cv_path,cv_text,_=await save_file(cv,folder)
    disc_path,disc_text,_=await save_file(disc,folder)
    li_path,li_extracted,_=await save_file(linkedin_pdf,folder)
    comp_path,comp_text,_=await save_file(disc_comparativo,folder)
    if comp_text:disc_text=(disc_text+'\n\nCOMPARATIVO DISC FORNECIDO:\n'+comp_text).strip()[:120000]
    linkedin_text=(linkedin_text.strip()+'\n'+li_extracted.strip()).strip()[:100000]
    token=secrets.token_urlsafe(24)
    with conn() as db:
        db.execute('''INSERT INTO candidates(id,vacancy_id,name,linkedin_url,cv_text,disc_text,linkedin_text,cv_file,disc_file,linkedin_file,token,status,created,invite_expires_at,revoked_at)
                      VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,NULL)''',
                   (cid,vacancy_id,name,linkedin_url[:700],cv_text[:120000],disc_text[:120000],linkedin_text,cv_path,disc_path,li_path,token,'convidado',now(),(datetime.now()+timedelta(days=14)).isoformat(timespec='seconds')))
    base=os.environ.get('ENTREVISTADOR_PUBLIC_URL','').strip().rstrip('/') or str(request.base_url).rstrip('/')
    return {'id':cid,'name':name,'invite':base+'/entrevista/'+token,'source_status':{'curriculo':bool(cv_text),'disc':bool(disc_text),'linkedin':bool(linkedin_text)}}

@APP.post('/api/admin/candidates/{cid}/materials')
async def update_candidate_materials(request:Request,cid:str,
    cv:Optional[UploadFile]=File(None),disc:Optional[UploadFile]=File(None),
    linkedin_pdf:Optional[UploadFile]=File(None),disc_comparativo:Optional[UploadFile]=File(None)):
    """Completa as fontes de um cadastro existente sem trocar o token da entrevista.
    Não substitui avaliações humanas já ratificadas ou retificadas.
    """
    must_admin(request)
    with conn() as db:
        old=db.execute('SELECT * FROM candidates WHERE id=?',(cid,)).fetchone()
        if not old:raise HTTPException(404,'Candidato não encontrado.')
        prev=db.execute('SELECT report_json FROM reports WHERE candidate_id=?',(cid,)).fetchone()
        if prev and json.loads(prev['report_json']).get('reviewed_count',0):
            raise HTTPException(409,'Há revisão humana registrada. Não substitua fontes sem preservar um novo ciclo de avaliação.')
    if not any(x and x.filename for x in (cv,disc,linkedin_pdf,disc_comparativo)):
        raise HTTPException(422,'Selecione ao menos um documento.')
    folder=f'candidatos/{cid}'
    cv_path,cv_txt,_=await save_file(cv,folder)
    disc_path,disc_txt,_=await save_file(disc,folder)
    link_path,li_txt,_=await save_file(linkedin_pdf,folder)
    _,comp_txt,_=await save_file(disc_comparativo,folder)
    disc_combined=((disc_txt if disc_path else old['disc_text'])+(('\n\nCOMPARATIVO DISC FORNECIDO:\n'+comp_txt) if comp_txt else '')).strip()[:120000]
    with conn() as db:
        db.execute("UPDATE candidates SET cv_text=?,disc_text=?,linkedin_text=?,cv_file=?,disc_file=?,linkedin_file=? WHERE id=?",
            (cv_txt[:120000] if cv_path else old['cv_text'],disc_combined,
             (old['linkedin_text']+'\n'+li_txt).strip()[:100000] if link_path else old['linkedin_text'],
             cv_path or old['cv_file'],disc_path or old['disc_file'],link_path or old['linkedin_file'],cid))
        db.execute('DELETE FROM reports WHERE candidate_id=?',(cid,))
    return {'ok':True,'message':'Fontes atualizadas. Gere novamente a análise antes de preparar o dossiê.',
            'extraido':{'curriculo':len(cv_txt),'disc':len(disc_combined),'linkedin':len(li_txt)}}

@APP.get('/api/admin/candidates/{cid}')
def candidate_detail(request:Request,cid:str):
    must_admin(request)
    with conn() as db:
        c=db.execute('SELECT * FROM candidates WHERE id=?',(cid,)).fetchone()
        if not c:raise HTTPException(404,'Candidato não encontrado.')
        c=dict(c)
    v=get_vacancy(c['vacancy_id']);q=json.loads(v['questions_json']);answers=get_answers(cid)
    with conn() as db:
        row=db.execute('SELECT report_json FROM reports WHERE candidate_id=?',(cid,)).fetchone()
    with conn() as db:
        tr=db.execute('SELECT id,status,progress,total,error,updated_at FROM transcription_jobs WHERE candidate_id=? ORDER BY created_at DESC LIMIT 1',(cid,)).fetchone()
    base=os.environ.get('ENTREVISTADOR_PUBLIC_URL','').strip().rstrip('/') or str(request.base_url).rstrip('/')
    return {'transcription_job':dict(tr) if tr else None,'id':cid,'name':c['name'],'status':c['status'],'linkedin_url':c['linkedin_url'],'cv_text':c['cv_text'][:30000], 'disc_text':c['disc_text'][:20000], 'linkedin_text':c['linkedin_text'][:20000], 'vacancy':v['title'],'questions':q,'answers':answers,'invite':base+'/entrevista/'+c['token'],'report':json.loads(row['report_json']) if row else None}

@APP.get('/api/invites/{token}')
def invite_data(token:str):
    c=get_candidate(token); v=get_vacancy(c['vacancy_id']);q=json.loads(v['questions_json']);a=get_answers(c['id'])
    return {'candidate':c['name'],'vacancy':v['title'],'status':c['status'],'questions':[{'id':x['id'],'question':x['question'],'category_label':x['category_label']} for x in q], 'answered':{k:bool(x['text'] or x['audio_file']) for k,x in a.items()}}

@APP.post('/api/invites/{token}/answer')
async def save_answer(token:str,question_id:str=Form(...),text:str=Form(''),audio:Optional[UploadFile]=File(None)):
    c=get_candidate(token)
    if c['status']=='concluido':raise HTTPException(403,'Entrevista já concluída.')
    v=get_vacancy(c['vacancy_id']);q=json.loads(v['questions_json'])
    if question_id not in {x['id'] for x in q}:raise HTTPException(422,'Pergunta desconhecida.')
    if bool(text.strip())==bool(audio and audio.filename):raise HTTPException(422,'Envie texto OU áudio.')
    saved='';mode='text';transcript=''
    if audio and audio.filename:
        content=await audio.read(12*1024*1024+1)
        if not content or len(content)>12*1024*1024:raise HTTPException(413,'Áudio vazio ou acima de 12 MB.')
        kind=(audio.content_type or '').lower()
        if not any(t in kind for t in ('audio/webm','audio/mp4','audio/ogg','audio/mpeg','audio/wav','audio/x-m4a','application/octet-stream')):raise HTTPException(415,'Formato de áudio não suportado.')
        ext=('.mp4' if 'mp4' in kind else '.ogg' if 'ogg' in kind else '.wav' if 'wav' in kind else '.webm')
        directory=UPLOADS/'audios'/c['id'];directory.mkdir(parents=True,exist_ok=True)
        saved=f'audios/{c["id"]}/{question_id}_{secrets.token_hex(6)}{ext}'
        (UPLOADS/saved).write_bytes(content);mode='audio'
    else:
        if len(text.strip())<3:raise HTTPException(422,'Digite uma resposta.')
        text=text.strip()[:10000]
    with conn() as db:
        db.execute('INSERT INTO answers(candidate_id,question_id,mode,text,transcript,audio_file,updated) VALUES(?,?,?,?,?,?,?) ON CONFLICT(candidate_id,question_id) DO UPDATE SET mode=excluded.mode,text=excluded.text,transcript=excluded.transcript,audio_file=excluded.audio_file,updated=excluded.updated',(c['id'],question_id,mode,text,transcript,saved,now()))
        db.execute('UPDATE candidates SET status=? WHERE id=?',('em_andamento',c['id']))
    return {'ok':True,'mode':mode}

@APP.post('/api/invites/{token}/complete')
def complete(token:str):
    c=get_candidate(token);v=get_vacancy(c['vacancy_id']);q=json.loads(v['questions_json']);a=get_answers(c['id'])
    missing=[x['id'] for x in q if x['id'] not in a or not (a[x['id']]['text'] or a[x['id']]['audio_file'])]
    if missing:raise HTTPException(422,'Há perguntas sem resposta: '+', '.join(missing))
    with conn() as db:db.execute('UPDATE candidates SET status=? WHERE id=?',('concluido',c['id']))
    job_id=queue_transcription(c['id'])
    return {'ok':True,'transcription':'queued' if job_id else 'not_required','message':'Entrevista concluída. Obrigado por participar.'}

@APP.post('/api/admin/candidates/{cid}/transcripts/{qid}')
async def add_transcript(request:Request,cid:str,qid:str):
    must_admin(request)
    body=await request.json();text=str(body.get('text','')).strip()[:12000]
    with conn() as db:
        row=db.execute('SELECT audio_file FROM answers WHERE candidate_id=? AND question_id=?',(cid,qid)).fetchone()
        if not row or not row['audio_file']:raise HTTPException(404,'Áudio da pergunta não encontrado.')
        db.execute('UPDATE answers SET transcript=?,updated=? WHERE candidate_id=? AND question_id=?',(text,now(),cid,qid))
    return {'ok':True}

@APP.post('/api/admin/candidates/{cid}/transcribe/{qid}',status_code=202)
def auto_transcribe(request:Request,cid:str,qid:str):
    """Enfileira uma transcrição. A resposta HTTP nunca espera o modelo terminar."""
    must_admin(request)
    with conn() as db:
        row=db.execute('SELECT audio_file FROM answers WHERE candidate_id=? AND question_id=?',(cid,qid)).fetchone()
    if not row or not row['audio_file']:raise HTTPException(404,'Áudio da pergunta não encontrado.')
    job=queue_transcription(cid,force=True)
    return {'status':'queued' if job else 'already_running_or_finished','job_id':job}

@APP.post('/api/admin/candidates/{cid}/transcribe-all',status_code=202)
def transcribe_all(request:Request,cid:str):
    must_admin(request)
    with conn() as db:
        if not db.execute('SELECT 1 FROM candidates WHERE id=?',(cid,)).fetchone():
            raise HTTPException(404,'Candidato não encontrado.')
    job=queue_transcription(cid,force=True)
    return {'status':'queued' if job else 'no_pending_audio','job_id':job}

@APP.get('/api/admin/candidates/{cid}/transcription-status')
def transcription_status(request:Request,cid:str):
    must_admin(request)
    with conn() as db:
        if not db.execute('SELECT 1 FROM candidates WHERE id=?',(cid,)).fetchone():
            raise HTTPException(404,'Candidato não encontrado.')
        job=db.execute('SELECT id,status,progress,total,error,updated_at FROM transcription_jobs WHERE candidate_id=? ORDER BY created_at DESC LIMIT 1',(cid,)).fetchone()
        pending=db.execute("SELECT COUNT(*) FROM answers WHERE candidate_id=? AND audio_file!='' AND (transcript IS NULL OR transcript='')",(cid,)).fetchone()[0]
    return {'job':dict(job) if job else None,'pending_audio':pending}

@APP.get('/api/admin/candidates/{cid}/audio/{qid}')
def get_audio(request:Request,cid:str,qid:str):
    must_admin(request)
    with conn() as db:
        a=db.execute('SELECT audio_file FROM answers WHERE candidate_id=? AND question_id=?',(cid,qid)).fetchone()
    if not a or not a['audio_file']:raise HTTPException(404,'Áudio não encontrado.')
    path=UPLOADS/a['audio_file']
    if not path.exists():raise HTTPException(404,'Arquivo ausente.')
    return FileResponse(path,media_type='audio/mp4' if path.suffix=='.mp4' else 'audio/ogg' if path.suffix=='.ogg' else 'audio/wav' if path.suffix=='.wav' else 'audio/webm')

from functools import lru_cache
@lru_cache(maxsize=1)
def get_whisper_model():
    """CPU e quantização int8. Modelo multilingue vem pré-carregado no Docker."""
    from faster_whisper import WhisperModel
    model_name=os.environ.get('ENTREVISTADOR_WHISPER_MODEL','/opt/whisper/tiny')
    return WhisperModel(model_name,device='cpu',compute_type='int8',cpu_threads=1,num_workers=1)

def transcribe_pending_audio(cid:str,job_id:str|None=None):
    """Executa apenas áudios pendentes e salva cada transcrição imediatamente.
    Uma transcrição vazia/ilegível interrompe o lote e não gera nota técnica.
    """
    with conn() as db:
        rows=db.execute("SELECT question_id,audio_file FROM answers WHERE candidate_id=? AND audio_file!='' AND (transcript IS NULL OR transcript='') ORDER BY updated",(cid,)).fetchall()
    if not rows:return 0
    model=get_whisper_model()
    completed=0
    for r in rows:
        path=UPLOADS/r['audio_file']
        if not path.is_file():raise RuntimeError('Arquivo de áudio não encontrado para '+r['question_id'])
        segments,info=model.transcribe(str(path),language='pt',vad_filter=True,beam_size=3,
                                        condition_on_previous_text=False)
        transcript=' '.join(str(seg.text).strip() for seg in segments).strip()[:12000]
        if not transcript:raise RuntimeError('Sem fala reconhecível na pergunta '+r['question_id']+'. Verifique o áudio.')
        with conn() as db:
            db.execute('UPDATE answers SET transcript=?,updated=? WHERE candidate_id=? AND question_id=? AND audio_file=?',
                       (transcript,now(),cid,r['question_id'],r['audio_file']))
            if job_id:
                db.execute('UPDATE transcription_jobs SET progress=?,updated_at=? WHERE id=?',(completed+1,now(),job_id))
        completed+=1
    return completed

def _do_transcription(cid:str,job_id:str):
    try:
        with conn() as db:db.execute('UPDATE transcription_jobs SET status=?,updated_at=? WHERE id=?',('running',now(),job_id))
        transcribed=transcribe_pending_audio(cid,job_id)
        with conn() as db:
            db.execute('UPDATE transcription_jobs SET status=?,progress=?,updated_at=? WHERE id=?',('finished',transcribed,now(),job_id))
    except Exception as err:
        with conn() as db:
            db.execute('UPDATE transcription_jobs SET status=?,error=?,updated_at=? WHERE id=?',('failed',str(err)[:350],now(),job_id))

def queue_transcription(cid:str,force:bool=False):
    """Agendamento idempotente, com estado persistente no SQLite."""
    with conn() as db:
        pending=db.execute("SELECT COUNT(*) FROM answers WHERE candidate_id=? AND audio_file!='' AND (transcript IS NULL OR transcript='')",(cid,)).fetchone()[0]
        if not pending:return None
        existing=db.execute("SELECT 1 FROM transcription_jobs WHERE candidate_id=? AND status IN ('queued','running') LIMIT 1",(cid,)).fetchone()
        if existing:return None
        job_id=uid()
        db.execute('INSERT INTO transcription_jobs VALUES(?,?,?,?,?,?,?,?)',
                   (job_id,cid,'queued',0,pending,'',now(),now()))
    POOL.submit(_do_transcription,cid,job_id)
    return job_id

def _do_analysis(cid:str,model:str,auto_transcribe:bool,job_id:str):
    try:
        with conn() as db:
            db.execute("UPDATE analysis_jobs SET status='running',updated_at=? WHERE id=?",(now(),job_id))
            row=db.execute('SELECT * FROM candidates WHERE id=?',(cid,)).fetchone()
            previous=db.execute('SELECT report_json FROM reports WHERE candidate_id=?',(cid,)).fetchone()
        if not row:raise ValueError('Candidato não encontrado.')
        if previous and json.loads(previous['report_json']).get('review_history'):
            raise ValueError('Não é permitido sobrescrever a análise já revisada.')
        c=dict(row);v=get_vacancy(c['vacancy_id']);questions=json.loads(v['questions_json'])
        transcribed=transcribe_pending_audio(cid) if auto_transcribe else 0
        answers=get_answers(cid)
        report=prepare_report(questions,answers,c['cv_text'],c['disc_text'],c['linkedin_text'],c['linkedin_url'],v['title'],c['name'],v['description'])
        def progress(done,total):
            with conn() as db:db.execute('UPDATE analysis_jobs SET progress=?,total=?,updated_at=? WHERE id=?',(done,total,now(),job_id))
        if model:
            report=evaluate_v9(report,c['cv_text'],c['linkedin_text'],v['description'],model,
                              os.environ.get('ENTREVISTADOR_OLLAMA_URL','http://127.0.0.1:11434'),progress=progress)
        else:
            report['pendencias'].append('Modelo local não configurado: nenhuma nota técnica preliminar atribuída.')
        # Redação documental preliminar: não gera nota e não aprova ninguém.
        # Pode ser revisada mesmo no plano Render gratuito sem Ollama.
        try:
            provisional=draft_from_sources(report,c['cv_text'],c['linkedin_text'],c['disc_text'])
            report['client_sections']={'tecnicas':provisional['tecnicas'],'comportamentais':provisional['comportamentais'],'recomendacao':''}
            report['draft_mode']=provisional['modo']
            report['draft_pending']={'tecnicas':provisional['validacoes_tecnicas'],'comportamentais':provisional['validacoes_comportamentais']}
        except ValueError as err:
            report['draft_error']=str(err)
        report['generated_at']=now()
        if transcribed:report['transcriptions_processed']=transcribed
        with conn() as db:
            db.execute("INSERT INTO reports VALUES(?,?,?) ON CONFLICT(candidate_id) DO UPDATE SET report_json=excluded.report_json,generated=excluded.generated",
                       (cid,json.dumps(report,ensure_ascii=False),now()))
            db.execute("UPDATE analysis_jobs SET status='finished',progress=?,total=?,updated_at=? WHERE id=?",
                       (len(report['criteria']),len(report['criteria']),now(),job_id))
    except Exception as error:
        with conn() as db:
            db.execute("UPDATE analysis_jobs SET status='failed',error=?,updated_at=? WHERE id=?",
                       (str(error)[:320],now(),job_id))

@APP.post('/api/admin/candidates/{cid}/analyze',status_code=202)
async def run_analysis(request:Request,cid:str,ollama_model:str=Form(''),auto_transcribe:bool=Form(True)):
    must_admin(request)
    with conn() as db:
        candidate=db.execute('SELECT id FROM candidates WHERE id=?',(cid,)).fetchone()
        if not candidate:raise HTTPException(404,'Candidato não encontrado.')
        existing=db.execute('SELECT report_json FROM reports WHERE candidate_id=?',(cid,)).fetchone()
        if existing and json.loads(existing['report_json']).get('review_history'):
            raise HTTPException(409,'Já existe uma revisão humana. Não é permitido substituir a análise.')
        active=db.execute("SELECT id FROM analysis_jobs WHERE candidate_id=? AND status IN ('queued','running')",(cid,)).fetchone()
        if active:raise HTTPException(409,'Análise já em andamento.')
        job_id=secrets.token_hex(12)
        db.execute('INSERT INTO analysis_jobs VALUES(?,?,?,?,?,?,?,?)',
                   (job_id,cid,'queued',0,0,'',now(),now()))
    with conn() as db:
        pend=db.execute("SELECT COUNT(*) FROM answers WHERE candidate_id=? AND audio_file!='' AND (transcript IS NULL OR transcript='')",(cid,)).fetchone()[0]
    if pend:
        # Revert an unused analysis job; transcription has its own queue.
        with conn() as db:db.execute('DELETE FROM analysis_jobs WHERE id=?',(job_id,))
        raise HTTPException(409,'Há áudio sem transcrição. Aguarde o processamento automático ou clique em Reprocessar transcrição.')
    model=(ollama_model.strip() or os.environ.get('ENTREVISTADOR_OLLAMA_MODEL','')).strip()[:100]
    POOL.submit(_do_analysis,cid,model,auto_transcribe,job_id)
    return {'job_id':job_id,'status':'queued','message':'Análise registrada; acompanhe o andamento.'}

@APP.get('/api/admin/jobs/{job_id}')
def get_job(request:Request,job_id:str):
    must_admin(request)
    with conn() as db:
        row=db.execute('SELECT * FROM analysis_jobs WHERE id=?',(job_id,)).fetchone()
        if not row:raise HTTPException(404,'Processamento não encontrado.')
        return dict(row)

@APP.post('/api/admin/candidates/{cid}/revoke-invite')
def revoke_invite(request:Request,cid:str):
    must_admin(request)
    with conn() as db:
        if not db.execute('SELECT id FROM candidates WHERE id=?',(cid,)).fetchone():raise HTTPException(404,'Não encontrado.')
        db.execute('UPDATE candidates SET revoked_at=? WHERE id=?',(now(),cid))
    return {'ok':True,'status':'revogado'}

@APP.delete('/api/admin/candidates/{cid}')
def delete_candidate(request:Request,cid:str):
    """Eliminação lógica da candidatura e física dos anexos locais, mediante ação administrativa."""
    must_admin(request)
    with conn() as db:
        cand=db.execute('SELECT id FROM candidates WHERE id=?',(cid,)).fetchone()
        if not cand:raise HTTPException(404,'Não encontrado.')
        if db.execute("SELECT id FROM analysis_jobs WHERE candidate_id=? AND status IN ('queued','running')",(cid,)).fetchone():
            raise HTTPException(409,'Aguarde o processamento atual terminar.')
        if db.execute("SELECT id FROM transcription_jobs WHERE candidate_id=? AND status IN ('queued','running')",(cid,)).fetchone():
            raise HTTPException(409,'Aguarde a transcrição terminar.')
        db.execute('DELETE FROM reports WHERE candidate_id=?',(cid,))
        db.execute('DELETE FROM answers WHERE candidate_id=?',(cid,))
        db.execute('DELETE FROM analysis_jobs WHERE candidate_id=?',(cid,))
        db.execute('DELETE FROM transcription_jobs WHERE candidate_id=?',(cid,))
        db.execute('DELETE FROM candidates WHERE id=?',(cid,))
    import shutil
    shutil.rmtree(UPLOADS/'candidatos'/cid,ignore_errors=True)
    shutil.rmtree(UPLOADS/'audios'/cid,ignore_errors=True)
    return {'ok':True,'message':'Candidatura e arquivos locais excluídos; backups precisam ser tratados separadamente.'}

@APP.post('/api/admin/candidates/{cid}/review')
async def review_report(request:Request,cid:str):
    must_admin(request);body=await request.json()
    with conn() as db:
        row=db.execute('SELECT report_json FROM reports WHERE candidate_id=?',(cid,)).fetchone()
        if not row:raise HTTPException(404,'Gere primeiro uma análise.')
        report=json.loads(row['report_json'])
        try:report=update_review(report,body.get('decisions',{}),body.get('comment',''))
        except ValueError as e:raise HTTPException(422,str(e))
        db.execute('UPDATE reports SET report_json=?,generated=? WHERE candidate_id=?',(json.dumps(report,ensure_ascii=False),now(),cid))
    return report

FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONT_BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
if Path(FONT).exists():
    pdfmetrics.registerFont(TTFont('EdSans',FONT));pdfmetrics.registerFont(TTFont('EdSans-Bold',FONT_BOLD));F='EdSans';B='EdSans-Bold'
else:F='Helvetica';B='Helvetica-Bold'

def texto_para_parecer(value):
    """Usa linguagem técnica na apresentação, preservando as fontes e a trilha interna.

    Mensagens operacionais de inferência não devem integrar o parecer entregue.
    O registro original continua disponível ao administrador para auditoria.
    """
    import re
    content=str(value if value is not None else 'Não informado')
    translations=(
        ('Aguardando avaliação contextual por IA local. Palavras-chave não atribuem notas.',
         'Avaliação preliminar não realizada; critério pendente de análise fundamentada.'),
        ('Nota descartada: a IA não citou trecho literal e relevante para este critério. Conferir manualmente possíveis sinônimos ou evidências não capturadas.',
         'Nota preliminar desconsiderada pela ausência de trecho literal pertinente ao critério. Conferir as fontes.'),
        ('Modelo não apresentou uma nota válida e justificável.',
         'Não há nota preliminar suficientemente fundamentada para este critério.'),
        ('A IA não retornou todos os critérios da vaga; itens restantes permanecem sem nota.',
         'Nem todos os critérios receberam avaliação fundamentada; os demais permanecem sem nota.'),
        ('IA local não configurada. Não foi criado score automático: a análise por palavras-chave não mede competência técnica.',
         'Não houve pontuação preliminar fundamentada. Correspondência de palavras-chave não demonstra competência técnica.'),
        ('Nota automática ratificada após conferência das fontes.',
         'Nota preliminar ratificada após conferência das fontes.'),
        ('Sem pendências automáticas adicionais.',
         'Sem outras pendências registradas.'),
        ('Nenhuma aprovação ou reprovação automática.',
         'O parecer não constitui decisão de contratação.'),
    )
    for before,after in translations:
        content=re.sub(re.escape(before),lambda m:after,content,flags=re.IGNORECASE)
    # Proteção adicional para trechos técnicos herdados de análises anteriores.
    content=re.sub(r'\b(?:IA|I\.A\.)\b', 'avaliação preliminar',content,flags=re.IGNORECASE)
    content=re.sub(r'\bOllama\b', 'avaliação',content,flags=re.IGNORECASE)
    content=re.sub(r'\bLLM\b', 'avaliação',content,flags=re.IGNORECASE)
    return content


def pdf_doc(report:dict)->bytes:
    """Dossiê com matriz de evidências e status de homologação, sem decisão automática."""
    buff=io.BytesIO()
    doc=SimpleDocTemplate(buff,pagesize=A4,rightMargin=1.8*cm,leftMargin=1.8*cm,topMargin=1.8*cm,bottomMargin=1.65*cm,title='Dossiê técnico de candidatura',author='Entrevistador Digital')
    navy=HexColor('#132B46');muted=HexColor('#52647B');light=HexColor('#F0F4F9')
    styles={
      'h1':ParagraphStyle('p7_h1',fontName=B,fontSize=15.3,leading=20,textColor=navy,spaceAfter=10),
      'h2':ParagraphStyle('p7_h2',fontName=B,fontSize=10.4,leading=14,textColor=navy,spaceBefore=11,spaceAfter=5),
      'body':ParagraphStyle('p7_body',fontName=F,fontSize=8.4,leading=12.1,alignment=TA_JUSTIFY,spaceAfter=5),
      'label':ParagraphStyle('p7_label',fontName=B,fontSize=8.5,leading=12.5,textColor=navy,spaceBefore=6,spaceAfter=3),
      'small':ParagraphStyle('p7_small',fontName=F,fontSize=7.5,leading=10.5,textColor=muted,spaceAfter=4),
    }
    def t(x,style='body'):
        return Paragraph(html.escape(texto_para_parecer(x)).replace('\n','<br/>'),styles[style])
    def val(x):return 'Não calculado' if x is None else str(x)+'%'
    el=[t('DOSSIÊ TÉCNICO DE CANDIDATURA','h1'),t('Avaliação profissional fundamentada em documentos e entrevista. Sujeita à revisão do recrutador.','small'),
        t('Candidato: '+report.get('candidate','')),t('Vaga: '+report.get('job_title','')),
        t('Situação: '+report.get('review_status','Pendente'))]
    data=[['INDICADOR','VALOR','COBERTURA'],['Aderência técnica evidenciada',val(report.get('technical_percent')),val(report.get('technical_coverage'))],
          ['Soft skills evidenciadas',val(report.get('behavioral_percent')),val(report.get('behavioral_coverage'))],
          ['Aderência profissional global',val(report.get('adherence_percent')),val(report.get('coverage_percent'))]]
    tbl=Table([[t(x,'label' if i==0 else 'small') for x in row] for i,row in enumerate(data)], colWidths=[8*cm,3.3*cm,3.25*cm],hAlign='LEFT')
    tbl.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),light),('LINEBELOW',(0,0),(-1,-1),.3,HexColor('#D9E0E8')),
        ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
    el.extend([Spacer(1,7),tbl,t('Método de cálculo e limites','h2'),t(report.get('score_method','')),
        t('Critério sem evidência fica sem nota e permanece no denominador. A cobertura acompanha a nota. A escala 0 é usada apenas quando há evidência explícita de não atendimento, não quando falta informação. Os relatos ainda precisam de validação.','small'),
        t('Matriz por critério','h2')])
    for c in report.get('criteria',[]):
        auto=c.get('auto_score');effective=c.get('score')
        head=f"{c['id']} | {c.get('category','')} | Peso {c['weight']} ({str(c.get('weight_percent'))+'%' if c.get('weight_percent') is not None else 'diferencial'}) | Nota preliminar: {str(auto)+'/4' if auto is not None else 'sem nota'} | Pontuação atual: {str(effective)+'/4' if effective is not None else 'sem nota'}"
        block=[t(head,'label'),t('Requisito: '+c.get('criterion','')),t('Origem na descrição: '+c.get('source_jd',''),'small')]
        if c.get('differential'):block.append(t('Diferencial, não eliminatório.','small'))
        if c.get('auto_reason'):block.append(t('Fundamentação preliminar: '+c['auto_reason']))
        quotes=c.get('verified_excerpts',[])
        for q in quotes[:4]:block.append(t('Trecho literal ('+q.get('source','')+'): '+q.get('excerpt',''),'small'))
        if c.get('review_decision') in ('ratificar','retificar'):
            block.append(t('Revisão do recrutador: '+c['review_decision']+'. '+c.get('review_justification','')))
        else:block.append(t('Revisão do recrutador pendente.','small'))
        for point in c.get('pending_validation',[])[:4]:block.append(t('Ponto a validar: '+point,'small'))
        if c.get('answer_mode')=='audio' and not c.get('answer'):block.append(t('Áudio sem transcrição: não analisado.','small'))
        el.extend(block)
    el.append(t('DISC: informação complementar','h2'))
    disc=report.get('disc',{})
    el.append(t('Leitura: '+disc.get('status','Sem informação')))
    for obs in disc.get('observations',[]):el.append(t(str(obs.get('dimension',''))+': '+str(obs.get('reported_value','')),'small'))
    el.append(t('As medidas DISC não compõem o score e não determinam elegibilidade. Qualquer interpretação deve considerar o instrumento e seu contexto de aplicação.','small'))
    el.append(t('Eliminatórios e condições da vaga','h2'))
    if report.get('eliminatorios_sugeridos'):
        for x in report['eliminatorios_sugeridos']:
            el.append(t(str(x.get('requisito',''))+' | '+str(x.get('estado','não confirmado'))+' | '+str(x.get('fundamento',''))))
    else:el.append(t('Não houve identificação contextual validada de eliminatórios. Validar manualmente as condições indispensáveis.'))
    el.append(t('Pendências e validações','h2'))
    for x in report.get('pendencias',[]):el.append(t('• '+x))
    if not report.get('pendencias'):el.append(t('Sem outras pendências registradas. Documentos e resultados declarados ainda exigem validação.'))
    el.append(t('Síntese da análise','h2'))
    if report.get('llm_summary'):el.append(t(report['llm_summary']))
    el.append(t(report.get('conclusion','')))
    if report.get('reviewer_comment'):
        el.extend([t('Parecer do recrutador','h2'),t(report['reviewer_comment'])])
    if report.get('review_history'):
        el.append(t('Histórico de ratificação / retificação','h2'))
        for h in report['review_history'][-30:]:
            el.append(t(str(h.get('date',''))+' | '+h['id']+' | '+h['decision']+' | Nota preliminar: '+str(h.get('auto_score'))+' | Nota após revisão: '+str(h.get('human_score') if h.get('human_score') is not None else h.get('auto_score'))+' | '+h.get('justification',''),'small'))
    el.extend([Spacer(1,10),HRFlowable(width='100%',thickness=.5,color=muted),t('Gerado: '+report.get('generated_at','')+' | '+report.get('review_status','Pendente de revisão humana'),'small')])
    def footer(canv,doc):
        canv.setFont(F,7.6);canv.setFillColor(muted)
        canv.drawString(1.8*cm,1.08*cm,'Entrevistador Digital | Parecer técnico' )
        canv.drawRightString(A4[0]-1.8*cm,1.08*cm,str(doc.page))
    doc.build(el,onFirstPage=footer,onLaterPages=footer)
    return buff.getvalue()

@APP.post('/api/admin/candidates/{cid}/client-draft')
async def generate_client_draft(request:Request,cid:str):
    must_admin(request)
    with conn() as db:
        c=db.execute('SELECT * FROM candidates WHERE id=?',(cid,)).fetchone()
        r=db.execute('SELECT report_json FROM reports WHERE candidate_id=?',(cid,)).fetchone()
    if not c or not r:raise HTTPException(404,'Gere primeiro a análise.')
    report=json.loads(r['report_json'])
    model=os.environ.get('ENTREVISTADOR_OLLAMA_MODEL','').strip()
    if model and report.get('reviewed_count',0)>0:
        try:
            return await run_in_threadpool(draft_sections,report,c['disc_text'],model,os.environ.get('ENTREVISTADOR_OLLAMA_URL','http://127.0.0.1:11434'))
        except Exception as ex:
            raise HTTPException(503,'Falha no rascunho contextual. Tente o modo documental ou revise a configuração: '+str(ex)[:150])
    try:
        return draft_from_sources(report,c['cv_text'],c['linkedin_text'],c['disc_text'])
    except ValueError as ex:
        raise HTTPException(422,str(ex))

@APP.post('/api/admin/candidates/{cid}/client-report')
async def save_client_report(request:Request,cid:str):
    """Salva textos destinados ao cliente, separados da matriz quantitativa interna."""
    must_admin(request)
    payload=await request.json()
    if not isinstance(payload,dict):raise HTTPException(422,'Conteúdo inválido.')
    def blocks(key):
        raw=payload.get(key,'')
        if not isinstance(raw,str):raise HTTPException(422,f'{key}: texto inválido.')
        if len(raw)>15000:raise HTTPException(422,f'{key}: acima do limite.')
        return [p.strip() for p in re.split(r'\n\s*\n',raw) if p.strip()][:18]
    tech=blocks('tecnicas')
    behavioral=blocks('comportamentais')
    reco=payload.get('recomendacao','')
    if not isinstance(reco,str) or len(reco)>7000:raise HTTPException(422,'Recomendação inválida.')
    with conn() as db:
        row=db.execute('SELECT report_json FROM reports WHERE candidate_id=?',(cid,)).fetchone()
        if not row:raise HTTPException(404,'Gere a análise antes de preparar o parecer do cliente.')
        report=json.loads(row['report_json'])
        report['client_sections']={'tecnicas':tech,'comportamentais':behavioral,'recomendacao':reco.strip()}
        report['client_edited_at']=now()
        db.execute('UPDATE reports SET report_json=?,generated=? WHERE candidate_id=?',(json.dumps(report,ensure_ascii=False),now(),cid))
    return {'ok':True,'client_sections':report['client_sections']}

@APP.get('/api/admin/candidates/{cid}/report.pdf')
def download_pdf(request:Request,cid:str):
    must_admin(request)
    with conn() as db:
        row=db.execute('SELECT report_json FROM reports WHERE candidate_id=?',(cid,)).fetchone()
    if not row:raise HTTPException(404,'Gere a análise antes de exportar.')
    report=json.loads(row['report_json'])
    sections=report.get('client_sections') or {}
    if not str(sections.get('recomendacao') or '').strip():
        raise HTTPException(409,'Registre e salve o parecer de recomendação do recrutador antes de exportar.')
    if not sections.get('tecnicas') or not sections.get('comportamentais'):
        raise HTTPException(409,'Revise e salve as seções técnica e comportamental antes de exportar.')
    if report.get('reviewed_count',0)<report.get('reviewable_count',0):
        raise HTTPException(409,'Conclua a revisão de todos os critérios, inclusive registrando sem nota onde necessário.')
    content=render_client_pdf(report)
    return Response(content,media_type='application/pdf',headers={'Content-Disposition':f'attachment; filename="parecer_cliente_{cid}.pdf"'})

@APP.get('/api/admin/candidates/{cid}/report-interno.pdf')
def download_internal_pdf(request:Request,cid:str):
    must_admin(request)
    with conn() as db:
        row=db.execute('SELECT report_json FROM reports WHERE candidate_id=?',(cid,)).fetchone()
    if not row:raise HTTPException(404,'Gere a análise antes de exportar.')
    content=pdf_doc(json.loads(row['report_json']))
    return Response(content,media_type='application/pdf',headers={'Content-Disposition':f'attachment; filename="avaliacao_interna_{cid}.pdf"'})

@APP.get('/api/admin/backup.zip')
def backup_local(request:Request):
    """Exportação manual para arquivar no Drive. Contém dados pessoais; proteção é responsabilidade do administrador."""
    must_admin(request)
    import zipfile
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.write(DB,'dados.sqlite3')
        total=0
        for file in UPLOADS.rglob('*'):
            if not file.is_file():continue
            total+=file.stat().st_size
            if total>200*1024*1024:raise HTTPException(413,'Backup acima de 200 MB; faça cópia pelo sistema de arquivos.')
            z.write(file,'arquivos/'+str(file.relative_to(UPLOADS)))
        z.writestr('LEIA-ME.txt','Cópia de arquivos de teste. Contém dados pessoais. NÃO compartilhar com candidatos. Não inclui a chave administrativa.\n')
    return Response(stream.getvalue(),media_type='application/zip',headers={'Content-Disposition':'attachment; filename="backup_entrevistador_digital.zip"'})

@APP.get('/api/admin/candidates/{cid}/report.json')
def download_json(request:Request,cid:str):
    must_admin(request)
    with conn() as db:row=db.execute('SELECT report_json FROM reports WHERE candidate_id=?',(cid,)).fetchone()
    if not row:raise HTTPException(404,'Gere a análise antes de exportar.')
    return Response(row['report_json'],media_type='application/json',headers={'Content-Disposition':f'attachment; filename="dossie_{cid}.json"'})

if __name__=='__main__':
    import uvicorn
    print('\nEntrevistador Digital V7: http://127.0.0.1:8765')
    print('Chave de acesso em:',ADMIN_KEY_FILE)
    print('Armazenamento de teste em:',DATA)
    uvicorn.run(APP,host=os.environ.get('ENTREVISTADOR_HOST','127.0.0.1'),port=int(os.environ.get('ENTREVISTADOR_PORT','8765')))

@APP.middleware('http')
async def public_security(request:Request,call_next):
    if PRODUCTION and request.method in ('POST','PUT','PATCH','DELETE'):
        from urllib.parse import urlsplit
        # O endereço público configurado serve para links; a validação CSRF
        # deve comparar o Origin ao Host efetivo da requisição. Uma variável
        # de ambiente desatualizada não deve impedir o login legítimo.
        real_host=(request.headers.get('host') or '').strip().lower()
        public_host=urlsplit(os.environ['ENTREVISTADOR_PUBLIC_URL'].strip()).netloc.lower()
        origin=(request.headers.get('origin') or '').strip()
        referer=(request.headers.get('referer') or '').strip()
        fetch_site=(request.headers.get('sec-fetch-site') or '').strip().lower()
        # Bloqueia Host desconhecido, e mantém o domínio temporário Render
        # permitido para o piloto; no domínio próprio, exige a variável.
        allowed_host=bool(real_host and (real_host==public_host or real_host=='entrevistador-digital.onrender.com'))
        reason=None
        if not allowed_host:
            reason='HOST'
        elif fetch_site in ('cross-site','same-site'):
            reason='FETCH_SITE'
        elif origin:
            o=urlsplit(origin)
            if o.scheme!='https' or o.netloc.lower()!=real_host:reason='ORIGIN'
        elif referer:
            r=urlsplit(referer)
            if r.scheme!='https' or r.netloc.lower()!=real_host:reason='REFERER'
        elif fetch_site not in ('','same-origin','none'):
            reason='FETCH_SITE_UNKNOWN'
        if reason:
            print('[SECURITY] POST bloqueado em '+request.url.path+'; motivo='+reason,flush=True)
            return JSONResponse({'detail':'Solicitação bloqueada por validação de origem. Código '+reason+'.'},status_code=403)
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['X-Frame-Options']='DENY'
    response.headers['Referrer-Policy']='no-referrer'
    response.headers['Permissions-Policy']='camera=(), geolocation=()'
    response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; media-src 'self' blob:; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
    response.headers['Cache-Control']='no-store' if (request.url.path.startswith('/api/') or request.url.path=='/' or request.url.path=='/static/app.js') else 'private, max-age=0'
    if PRODUCTION:response.headers['Strict-Transport-Security']='max-age=31536000; includeSubDomains'
    return response

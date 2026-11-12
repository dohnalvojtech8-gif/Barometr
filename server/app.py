"""BAROMETR accounts API. PostgreSQL in production; explicit SQLite only for tests."""
import os, json, time, secrets, hashlib, hmac, re, uuid, sqlite3, unicodedata
from pathlib import Path
from contextlib import contextmanager
from functools import wraps
from flask import Flask, request, jsonify, g, send_from_directory, make_response

ROOT=Path(__file__).resolve().parent.parent
WEB=Path(__file__).resolve().parent/'web'
DATABASE_URL=os.environ.get('DATABASE_URL')
TEST_DB=os.environ.get('BAROMETR_TEST_DB')
if not DATABASE_URL and not TEST_DB: raise RuntimeError('DATABASE_URL is required')
SESSION_DAYS=7
COOKIE='barometr_session'
SECURE=os.environ.get('BAROMETR_TEST_HTTP')!='1'
app=Flask(__name__,static_folder=None)
app.config.update(MAX_CONTENT_LENGTH=512*1024,JSON_SORT_KEYS=False)

def connect():
    if TEST_DB:
        c=sqlite3.connect(TEST_DB,timeout=15);c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON');return c
    import psycopg
    from psycopg.rows import dict_row
    return psycopg.connect(DATABASE_URL,row_factory=dict_row,connect_timeout=10)
def execute(c,sql,args=()): return c.execute(sql.replace('%s','?') if TEST_DB else sql,args)
@contextmanager
def db():
    c=connect()
    try:
        if TEST_DB:c.execute('BEGIN IMMEDIATE')
        yield c;c.commit()
    except: c.rollback();raise
    finally:c.close()
def one(c,sql,args=()):
    r=execute(c,sql,args).fetchone();return dict(r) if r else None
def allrows(c,sql,args=()):return [dict(r) for r in execute(c,sql,args).fetchall()]
def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def uid():return str(uuid.uuid4())
def password_hash(value):
    salt=secrets.token_hex(16);key=hashlib.scrypt(value.encode(),salt=bytes.fromhex(salt),n=16384,r=8,p=1).hex();return 'scrypt$'+salt+'$'+key
def password_ok(value,hashed):
    try:
        _,salt,key=hashed.split('$');got=hashlib.scrypt(value.encode(),salt=bytes.fromhex(salt),n=16384,r=8,p=1).hex();return hmac.compare_digest(got,key)
    except (ValueError,TypeError):return False
DUMMY=password_hash(secrets.token_urlsafe(24))
SCHEMA=[
'''CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, username TEXT NOT NULL, username_key TEXT UNIQUE NOT NULL, first_name TEXT NOT NULL, last_name TEXT NOT NULL, password_hash TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('admin','user')), status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','suspended')), created_at DOUBLE PRECISION NOT NULL, last_login DOUBLE PRECISION, last_seen DOUBLE PRECISION, login_count INTEGER NOT NULL DEFAULT 0, state_json TEXT NOT NULL DEFAULT '{}')''',
'''CREATE TABLE IF NOT EXISTS scan_photos (id TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,jpeg TEXT NOT NULL,created_at DOUBLE PRECISION NOT NULL)''',
'''CREATE TABLE IF NOT EXISTS sessions (token_hash TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,csrf TEXT NOT NULL,created_at DOUBLE PRECISION NOT NULL,expires_at DOUBLE PRECISION NOT NULL)''',
'''CREATE TABLE IF NOT EXISTS invitations (id TEXT PRIMARY KEY,code_hash TEXT UNIQUE NOT NULL,label TEXT NOT NULL,created_by TEXT REFERENCES users(id) ON DELETE SET NULL,created_at DOUBLE PRECISION NOT NULL,expires_at DOUBLE PRECISION NOT NULL,max_uses INTEGER NOT NULL,used_count INTEGER NOT NULL DEFAULT 0,revoked INTEGER NOT NULL DEFAULT 0)''',
'''CREATE TABLE IF NOT EXISTS invitation_uses (id TEXT PRIMARY KEY,invite_id TEXT REFERENCES invitations(id) ON DELETE CASCADE,user_id TEXT REFERENCES users(id) ON DELETE CASCADE,used_at DOUBLE PRECISION NOT NULL)''',
'''CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY,user_id TEXT REFERENCES users(id) ON DELETE CASCADE,action TEXT NOT NULL,detail TEXT NOT NULL,created_at DOUBLE PRECISION NOT NULL)''',
'''CREATE TABLE IF NOT EXISTS unlocks (user_id TEXT REFERENCES users(id) ON DELETE CASCADE,product_id TEXT NOT NULL,created_at DOUBLE PRECISION NOT NULL,PRIMARY KEY(user_id,product_id))''',
'''CREATE TABLE IF NOT EXISTS rate_buckets (bucket TEXT PRIMARY KEY,started_at DOUBLE PRECISION NOT NULL,attempts INTEGER NOT NULL)''',
'CREATE INDEX IF NOT EXISTS events_user_time ON events(user_id,created_at)',
'CREATE INDEX IF NOT EXISTS sessions_user ON sessions(user_id)',
'CREATE INDEX IF NOT EXISTS users_last_seen ON users(last_seen)']
def audit(c,user_id,action,detail=''):
    execute(c,'INSERT INTO events (id,user_id,action,detail,created_at) VALUES (%s,%s,%s,%s,%s)',(uid(),user_id,action,detail[:240],time.time()))
def init_db():
    with db() as c:
        for sql in SCHEMA:execute(c,sql)
        for number in (1,2):
            name=os.environ.get(f'ADMIN{number}_USERNAME');password=os.environ.get(f'ADMIN{number}_PASSWORD')
            if name and password:
                execute(c,"INSERT INTO users (id,username,username_key,first_name,last_name,password_hash,role,created_at) VALUES (%s,%s,%s,%s,%s,%s,'admin',%s) ON CONFLICT (username_key) DO NOTHING",(uid(),name,name.casefold(),name,'',password_hash(password),time.time()))
        execute(c,'DELETE FROM sessions WHERE expires_at < %s',(time.time(),))
        execute(c,'DELETE FROM events WHERE created_at < %s',(time.time()-90*86400,))
        execute(c,'DELETE FROM rate_buckets WHERE started_at < %s',(time.time()-86400,))
init_db()
raw=(ROOT/'aplikace/catalog-data.js').read_text()
CATALOG=json.loads(raw.split(' = ',1)[1].rstrip(';\n'))
PRODUCTS={p['id']:p for p in CATALOG['products']}

class ApiError(Exception):
    def __init__(self,message,status=400):self.message=message;self.status=status
@app.errorhandler(ApiError)
def api_error(e):return jsonify(error=e.message),e.status
@app.errorhandler(413)
def too_large(e):return jsonify(error='Požadavek je příliš velký.'),413
@app.errorhandler(Exception)
def unexpected(e):
    from werkzeug.exceptions import HTTPException
    if isinstance(e,HTTPException):return jsonify(error='Požadavek nelze zpracovat.'),e.code
    app.logger.error('Unhandled request failure: %s',type(e).__name__)
    return jsonify(error='Dočasná chyba serveru. Zkuste to znovu.'),500
_last_cleanup=0
@app.before_request
def cleanup_expired():
    global _last_cleanup
    now=time.time()
    if now-_last_cleanup>3600:
        with db() as c:
            execute(c,'DELETE FROM events WHERE created_at < %s',(now-90*86400,))
            execute(c,'DELETE FROM sessions WHERE expires_at < %s',(now,))
            execute(c,'DELETE FROM rate_buckets WHERE started_at < %s',(now-86400,))
        _last_cleanup=now

@app.before_request
def protect_origin():
    if request.path.startswith('/api/') and request.method in ('POST','PUT','PATCH','DELETE'):
        if request.headers.get('Origin') and request.headers['Origin'].rstrip('/')!=request.host_url.rstrip('/'):
            # Render TLS terminates at the proxy, so compare host and require HTTPS in production.
            from urllib.parse import urlparse
            origin=urlparse(request.headers['Origin'])
            if origin.netloc!=request.host or (SECURE and origin.scheme!='https'):raise ApiError('Nepovolený původ požadavku.',403)
        if request.mimetype!='application/json':raise ApiError('Očekáván JSON požadavek.',415)
@app.after_request
def headers(response):
    response.headers['X-Content-Type-Options']='nosniff';response.headers['X-Frame-Options']='DENY';response.headers['Referrer-Policy']='strict-origin-when-cross-origin'
    response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' https: data:; connect-src 'self'; media-src 'self' blob:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    if request.path.startswith('/api/') or request.path=='/':response.headers['Cache-Control']='no-store'
    return response

def body():
    value=request.get_json(silent=True)
    if not isinstance(value,dict):raise ApiError('Neplatný požadavek.')
    return value
def textfield(data,key,minimum=1,maximum=64):
    v=data.get(key)
    if not isinstance(v,str):raise ApiError('Vyplňte všechna povinná pole.')
    v=unicodedata.normalize('NFKC',v).strip()
    if len(v)<minimum or len(v)>maximum or any(ord(x)<32 for x in v):raise ApiError('Zkontrolujte délku a obsah polí.')
    return v
def authenticated(admin=False):
    def decorator(fn):
        @wraps(fn)
        def wrapped(*args,**kwargs):
            token=request.cookies.get(COOKIE,'')
            with db() as c:
                row=one(c,"SELECT u.*,s.csrf,s.token_hash FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=%s AND s.expires_at>%s AND u.status='active'",(digest(token),time.time()))
                if not row:raise ApiError('Přihlaste se prosím.',401)
                if admin and row['role']!='admin':raise ApiError('Tato akce je dostupná pouze administrátorům.',403)
                if request.method in ('POST','PUT','PATCH','DELETE') and not hmac.compare_digest(request.headers.get('X-CSRF-Token',''),row['csrf']):raise ApiError('Obnovte stránku a zkuste to znovu.',403)
                if not row['last_seen'] or time.time()-row['last_seen']>45:execute(c,'UPDATE users SET last_seen=%s WHERE id=%s',(time.time(),row['id']))
                g.user=row
            return fn(*args,**kwargs)
        return wrapped
    return decorator

def public_user(u):return {k:u[k] for k in ('id','username','first_name','last_name','role','status','created_at','last_login','last_seen','login_count')}
def rate_limit(keys,max_attempts=8,window=900):
    now=time.time()
    with db() as c:
        for key in keys:
            key=digest(key)
            execute(c,'INSERT INTO rate_buckets (bucket,started_at,attempts) VALUES (%s,%s,1) ON CONFLICT (bucket) DO UPDATE SET attempts=CASE WHEN rate_buckets.started_at<%s THEN 1 ELSE rate_buckets.attempts+1 END,started_at=CASE WHEN rate_buckets.started_at<%s THEN %s ELSE rate_buckets.started_at END',(key,now,now-window,now-window,now))
            if one(c,'SELECT attempts FROM rate_buckets WHERE bucket=%s',(key,))['attempts']>max_attempts:raise ApiError('Příliš mnoho pokusů. Zkuste to za 15 minut.',429)
def client_ip():return request.headers.get('X-Forwarded-For',request.remote_addr or 'unknown').split(',')[-1].strip()
def session_response(c,u):
    token=secrets.token_urlsafe(32);csrf=secrets.token_urlsafe(24);now=time.time()
    execute(c,'INSERT INTO sessions (token_hash,user_id,csrf,created_at,expires_at) VALUES (%s,%s,%s,%s,%s)',(digest(token),u['id'],csrf,now,now+SESSION_DAYS*86400))
    execute(c,'UPDATE users SET last_login=%s,last_seen=%s,login_count=login_count+1 WHERE id=%s',(now,now,u['id']))
    audit(c,u['id'],'login','Úspěšné přihlášení')
    response=jsonify(ok=True);response.set_cookie(COOKIE,token,max_age=SESSION_DAYS*86400,httponly=True,secure=SECURE,samesite='Lax',path='/');return response
@app.post('/api/login')
def login():
    data=body();username=textfield(data,'username',1,64);password=data.get('password','')
    if not isinstance(password,str) or len(password)>128:raise ApiError('Nesprávné přihlašovací údaje.',401)
    rate_limit(['login-name:'+username.casefold()],5);rate_limit(['login-ip:'+client_ip()],40)
    with db() as c:
        u=one(c,'SELECT * FROM users WHERE username_key=%s',(username.casefold(),))
        ok=password_ok(password,u['password_hash'] if u else DUMMY)
        if not u or not ok or u['status']!='active':
            if u:audit(c,u['id'],'login_failed','Neúspěšný pokus o přihlášení')
            # Return instead of raising so the attempted-login audit is committed.
            return jsonify(error='Nesprávné přihlašovací údaje nebo zablokovaný účet.'),401
        execute(c,'DELETE FROM rate_buckets WHERE bucket=%s',(digest('login-name:'+username.casefold()),))
        return session_response(c,u)
@app.post('/api/register')
def register():
    data=body();first=textfield(data,'firstName');last=textfield(data,'lastName');username=textfield(data,'username',3,32);password=data.get('password','');code=textfield(data,'inviteCode',8,100).upper().replace(' ','')
    if not re.fullmatch(r'[A-Za-z0-9_.-]{3,32}',username):raise ApiError('Uživatelské jméno: 3–32 písmen bez diakritiky, číslic nebo znaků . _ -')
    if not isinstance(password,str) or not 8<=len(password)<=128:raise ApiError('Heslo musí mít 8–128 znaků.')
    rate_limit(['register:'+client_ip()],15)
    with db() as c:
        if one(c,'SELECT id FROM users WHERE username_key=%s',(username.casefold(),)):raise ApiError('Toto uživatelské jméno je již obsazené.',409)
        invite=one(c,'SELECT * FROM invitations WHERE code_hash=%s',(digest(code),))
        if not invite:raise ApiError('Pozvánka je neplatná, použitá nebo vypršela.')
        count=execute(c,'UPDATE invitations SET used_count=used_count+1 WHERE id=%s AND revoked=0 AND expires_at>%s AND used_count<max_uses',(invite['id'],time.time())).rowcount
        if count!=1:raise ApiError('Pozvánka je neplatná, použitá nebo vypršela.')
        id=uid();execute(c,"INSERT INTO users (id,username,username_key,first_name,last_name,password_hash,role,created_at) VALUES (%s,%s,%s,%s,%s,%s,'user',%s)",(id,username,username.casefold(),first,last,password_hash(password),time.time()))
        execute(c,'INSERT INTO invitation_uses (id,invite_id,user_id,used_at) VALUES (%s,%s,%s,%s)',(uid(),invite['id'],id,time.time()))
        audit(c,id,'registered','Registrace pomocí pozvánky')
        return session_response(c,one(c,'SELECT * FROM users WHERE id=%s',(id,)))
@app.get('/api/me')
@authenticated()
def me():
    with db() as c:
        unlocked=allrows(c,'SELECT product_id,created_at FROM unlocks WHERE user_id=%s',(g.user['id'],))
        state=json.loads(g.user['state_json']);state.update(unlocks={r['product_id']:{'reason':'admin','paid':0,'at':r['created_at']*1000} for r in unlocked},ownerPreview=g.user['role']=='admin')
        return jsonify(user=public_user(g.user),csrf=g.user['csrf'],state=state)
@app.post('/api/logout')
@authenticated()
def logout():
    with db() as c:execute(c,'DELETE FROM sessions WHERE token_hash=%s',(g.user['token_hash'],));audit(c,g.user['id'],'logout','Odhlášení')
    r=jsonify(ok=True);r.delete_cookie(COOKIE,path='/');return r
@app.get('/api/catalog')
@authenticated()
def catalog():return jsonify(CATALOG)
@app.post('/api/unlocks')
@authenticated(admin=True)
def unlock():
    id=body().get('productId')
    if id not in PRODUCTS:raise ApiError('Produkt neexistuje.',404)
    with db() as c:
        n=execute(c,'INSERT INTO unlocks (user_id,product_id,created_at) VALUES (%s,%s,%s) ON CONFLICT (user_id,product_id) DO NOTHING',(g.user['id'],id,time.time())).rowcount
        if n:audit(c,g.user['id'],'product_unlocked',PRODUCTS[id]['name'])
    return jsonify(ok=True)
@app.get('/api/products/<id>')
@authenticated()
def product(id):
    if id not in PRODUCTS:raise ApiError('Produkt neexistuje.',404)
    with db() as c:
        if g.user['role']!='admin' or not one(c,'SELECT product_id FROM unlocks WHERE user_id=%s AND product_id=%s',(g.user['id'],id)):raise ApiError('Otevření lahví je pro testovací uživatele zatím vypnuté.',403)
        audit(c,g.user['id'],'product_opened',PRODUCTS[id]['name'])
    return jsonify(PRODUCTS[id])
@app.get('/api/barcode/<code>')
@authenticated()
def barcode_lookup(code):
    if not re.fullmatch(r'(?:[0-9]{8}|[0-9]{12,14})',code):raise ApiError('Neplatný čárový kód.')
    digits=[int(x) for x in code]
    if (sum(digits[-2::-2])*3+sum(digits[-3::-2])+digits[-1])%10:raise ApiError('Nesouhlasí kontrolní číslice kódu.')
    rate_limit(['barcode:'+g.user['id']],40,60)
    from urllib.request import Request,urlopen
    from urllib.error import URLError
    url='https://world.openfoodfacts.org/api/v2/product/'+code+'.json?fields=product_name,brands,quantity,product_quantity,product_quantity_unit'
    try:
        with urlopen(Request(url,headers={'User-Agent':'Barometr/0.5 (bottle inventory; https://github.com/dohnalvojtech8-gif/Barometr)'}),timeout=7) as response:
            data=json.loads(response.read(65536))
    except (URLError,TimeoutError,ValueError,OSError):raise ApiError('Online databáze není dostupná. Ověřte etiketu a objem ručně.',503)
    if not isinstance(data,dict):raise ApiError('Online databáze vrátila neplatnou odpověď.',503)
    p=data.get('product',{})
    if data.get('status')!=1 or not isinstance(p,dict) or not p.get('product_name'):return jsonify(found=False,code=code)
    return jsonify(found=True,code=code,name=str(p.get('product_name',''))[:200],brands=str(p.get('brands',''))[:200],quantity=str(p.get('quantity',''))[:80],source='Open Food Facts',url='https://world.openfoodfacts.org/product/'+code)

@app.put('/api/scan-photos/<photo_id>')
@authenticated(admin=True)
def put_scan_photo(photo_id):
    import base64,binascii
    if not re.fullmatch(r'[a-zA-Z0-9-]{1,100}',photo_id):raise ApiError('Neplatné ID snímku.')
    data=body();image=data.get('image','')
    if not isinstance(image,str) or not image.startswith('data:image/jpeg;base64,') or len(image)>300000:raise ApiError('Neplatný nebo příliš velký snímek.')
    try:raw=base64.b64decode(image.split(',',1)[1],validate=True)
    except (ValueError,binascii.Error):raise ApiError('Neplatný snímek.')
    if not raw.startswith(b'\xff\xd8') or not raw.endswith(b'\xff\xd9'):raise ApiError('Snímek musí být JPEG.')
    with db() as c:
        existing=one(c,'SELECT user_id FROM scan_photos WHERE id=%s',(photo_id,))
        if existing and existing['user_id']!=g.user['id']:raise ApiError('Snímek není dostupný.',404)
        execute(c,'INSERT INTO scan_photos (id,user_id,jpeg,created_at) VALUES (%s,%s,%s,%s) ON CONFLICT (id) DO UPDATE SET jpeg=excluded.jpeg WHERE scan_photos.user_id=excluded.user_id',(photo_id,g.user['id'],image,time.time()))
    return jsonify(id=photo_id)
@app.get('/api/scan-photos/<photo_id>')
@authenticated()
def get_scan_photo(photo_id):
    import base64
    with db() as c:photo=one(c,'SELECT jpeg FROM scan_photos WHERE id=%s AND user_id=%s',(photo_id,g.user['id']))
    if not photo:raise ApiError('Snímek nebyl nalezen.',404)
    response=make_response(base64.b64decode(photo['jpeg'].split(',',1)[1]));response.headers['Content-Type']='image/jpeg';response.headers['Cache-Control']='private, no-store';return response

@app.put('/api/state')
@authenticated()
def put_state():
    data=body();clean={}
    for key in ('cycle','closing'):
        if key in data:clean[key]=data[key]
    if clean.get('cycle','Měsíční') not in ('Denní','Týdenní','Měsíční'):raise ApiError('Neplatný cyklus.')
    if not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d',str(clean.get('closing','04:00'))):raise ApiError('Neplatný čas.')
    old=json.loads(g.user['state_json'])
    plan=data.get('inventoryPlan',old.get('inventoryPlan',{'entries':[]}))
    if not isinstance(plan,dict) or not isinstance(plan.get('entries'),list) or len(plan['entries'])>500:raise ApiError('Neplatný plán inventury.')
    if plan.get('runId') is not None and (not isinstance(plan['runId'],str) or not re.fullmatch(r'[a-zA-Z0-9-]{1,48}',plan['runId'])):raise ApiError('Neplatné kolo inventury.')
    if g.user['role']!='admin' and plan['entries']:raise ApiError('Inventura zatím není pro uživatele povolená.',403)
    if g.user['role']!='admin' and (data.get('rows') or data.get('records')):raise ApiError('Evidence lahví zatím není pro uživatele povolená.',403)
    if g.user['role']=='admin':
        rows=data.get('rows',[]);records=data.get('records',[])
        if not isinstance(rows,list) or len(rows)>500 or not isinstance(records,list) or len(records)>3000:raise ApiError('Příliš mnoho záznamů.')
        with db() as c:ids={r['product_id'] for r in allrows(c,'SELECT product_id FROM unlocks WHERE user_id=%s',(g.user['id'],))}
        seen=set()
        for row in rows:
            if not isinstance(row,dict) or row.get('productId') not in ids or row.get('id') in seen:raise ApiError('Neplatná nebo neodemčená lahev.')
            seen.add(row.get('id'));p=PRODUCTS[row['productId']]
            if row.get('capacity') not in [v['ml'] for v in p['variants']]:raise ApiError('Neplatný objem lahve.')
            for k in ('ml','start','sold40','sold20','otherMl'):
                if type(row.get(k)) not in (int,float) or not 0<=row[k]<=100000:raise ApiError('Neplatné množství.')
            if row['ml']>row['capacity'] or row['start']>row['capacity']:raise ApiError('Objem překračuje kapacitu lahve.')
            if not isinstance(row.get('label'),str) or len(row['label'])>80:raise ApiError('Neplatné označení lahve.')
        for r in records:
            if not isinstance(r,dict) or r.get('productId') not in ids or type(r.get('ml')) not in (int,float):raise ApiError('Neplatná historie.')
        entry_ids=set()
        for entry in plan['entries']:
            if not isinstance(entry,dict) or not isinstance(entry.get('id'),str) or not re.fullmatch(r'[a-zA-Z0-9-]{1,48}',entry['id']) or entry['id'] in entry_ids:raise ApiError('Neplatná položka plánu.')
            entry_ids.add(entry['id'])
            if entry.get('productId') not in ids or entry.get('capacity') not in [v['ml'] for v in PRODUCTS[entry['productId']]['variants']]:raise ApiError('Neplatný produkt nebo objem v plánu.')
            if not isinstance(entry.get('label',''),str) or len(entry.get('label',''))>80:raise ApiError('Neplatný název v plánu.')
            if entry.get('status','pending') not in ('pending','done','skipped'):raise ApiError('Neplatný stav plánu.')
            if entry.get('rowId') and entry['rowId'] not in seen:raise ApiError('Lahev plánu není v inventuře.')
        clean.update(rows=rows,records=records)
    else:clean.update(rows=[],records=[])
    clean['inventoryPlan']=plan
    with db() as c:
        execute(c,'UPDATE users SET state_json=%s WHERE id=%s',(json.dumps(clean,ensure_ascii=False),g.user['id']))
        if clean.get('rows')!=old.get('rows') or clean.get('records')!=old.get('records'):audit(c,g.user['id'],'inventory_saved','Uložení inventury')
        elif clean.get('cycle')!=old.get('cycle') or clean.get('closing')!=old.get('closing'):audit(c,g.user['id'],'settings_changed','Změna nastavení')
    return jsonify(ok=True)
@app.post('/api/activity')
@authenticated()
def activity():
    data=body();action=data.get('action');labels={'catalog':'Otevření katalogu','library':'Moje lahve','overview':'Přehled inventury','history':'Historie měření','settings':'Nastavení','users':'Správa uživatelů','search':'Hledání v katalogu','heartbeat':'Aktivní aplikace'}
    if action not in labels:raise ApiError('Neplatná událost.')
    if action=='users' and g.user['role']!='admin':raise ApiError('Zakázáno.',403)
    with db() as c:
        if action!='heartbeat':
            last=one(c,'SELECT created_at FROM events WHERE user_id=%s AND action=%s ORDER BY created_at DESC LIMIT 1',(g.user['id'],'view_'+action))
            if not last or time.time()-last['created_at']>20:audit(c,g.user['id'],'view_'+action,labels[action])
    return jsonify(ok=True)
@app.get('/api/admin/users')
@authenticated(admin=True)
def users_list():
    with db() as c:
        users=allrows(c,'SELECT id,username,first_name,last_name,role,status,created_at,last_login,last_seen,login_count FROM users ORDER BY created_at DESC')
        counts={r['user_id']:r['n'] for r in allrows(c,'SELECT user_id,COUNT(*) AS n FROM events WHERE created_at>%s GROUP BY user_id',(time.time()-7*86400,))}
        for u in users:u['activity7d']=counts.get(u['id'],0)
    return jsonify(users=users)
@app.get('/api/admin/users/<id>')
@authenticated(admin=True)
def user_detail(id):
    limit=min(max(request.args.get('limit',100,type=int),1),200);offset=max(request.args.get('offset',0,type=int),0)
    with db() as c:
        u=one(c,'SELECT * FROM users WHERE id=%s',(id,))
        if not u:raise ApiError('Účet neexistuje.',404)
        total=one(c,'SELECT COUNT(*) AS n FROM events WHERE user_id=%s',(id,))['n']
        events=allrows(c,'SELECT id,action,detail,created_at FROM events WHERE user_id=%s ORDER BY created_at DESC LIMIT %s OFFSET %s',(id,limit,offset))
        sessions=one(c,'SELECT COUNT(*) AS n FROM sessions WHERE user_id=%s AND expires_at>%s',(id,time.time()))['n']
    return jsonify(user=public_user(u),events=events,total=total,activeSessions=sessions)
@app.post('/api/admin/invites')
@authenticated(admin=True)
def invite_create():
    data=body();label=str(data.get('label','Pozvánka'))[:80].strip() or 'Pozvánka';days=data.get('days',7);uses=data.get('maxUses',1)
    if type(days) is not int or not 1<=days<=30 or type(uses) is not int or not 1<=uses<=50:raise ApiError('Platnost 1–30 dní, počet použití 1–50.')
    code='BM-'+secrets.token_hex(12).upper();id=uid();now=time.time()
    with db() as c:
        execute(c,'INSERT INTO invitations (id,code_hash,label,created_by,created_at,expires_at,max_uses) VALUES (%s,%s,%s,%s,%s,%s,%s)',(id,digest(code),label,g.user['id'],now,now+days*86400,uses));audit(c,g.user['id'],'invite_created','Vygenerování registrační pozvánky')
    return jsonify(id=id,code=code,expiresAt=now+days*86400,maxUses=uses)
@app.get('/api/admin/invites')
@authenticated(admin=True)
def invite_list():
    with db() as c:return jsonify(invites=allrows(c,'SELECT i.id,i.label,i.created_at,i.expires_at,i.max_uses,i.used_count,i.revoked,u.username AS creator FROM invitations i LEFT JOIN users u ON i.created_by=u.id ORDER BY i.created_at DESC LIMIT 100'))
@app.post('/api/admin/invites/<id>/revoke')
@authenticated(admin=True)
def invite_revoke(id):
    with db() as c:execute(c,'UPDATE invitations SET revoked=1 WHERE id=%s',(id,));audit(c,g.user['id'],'invite_revoked','Zrušení pozvánky')
    return jsonify(ok=True)
@app.post('/api/admin/users/<id>/status')
@authenticated(admin=True)
def user_status(id):
    status=body().get('status')
    if status not in ('active','suspended'):raise ApiError('Neplatný stav.')
    with db() as c:
        target=one(c,'SELECT * FROM users WHERE id=%s',(id,))
        if not target:raise ApiError('Účet neexistuje.',404)
        if target['role']=='admin':raise ApiError('Administrátory zde nelze blokovat.',403)
        execute(c,'UPDATE users SET status=%s WHERE id=%s',(status,id));execute(c,'DELETE FROM sessions WHERE user_id=%s',(id,));audit(c,g.user['id'],'user_status_changed',('Zablokování' if status=='suspended' else 'Obnovení')+' účtu '+target['username'])
    return jsonify(ok=True)
@app.delete('/api/admin/users/<id>')
@authenticated(admin=True)
def user_delete(id):
    confirmation=body().get('confirmation')
    with db() as c:
        target=one(c,'SELECT * FROM users WHERE id=%s',(id,))
        if not target:raise ApiError('Účet neexistuje.',404)
        if target['role']=='admin':raise ApiError('Administrátory zde nelze smazat.',403)
        if confirmation!=target['username']:raise ApiError('Pro potvrzení zadejte přesné uživatelské jméno.')
        execute(c,'DELETE FROM users WHERE id=%s',(id,));audit(c,g.user['id'],'user_deleted','Odstranění testovacího účtu a jeho záznamů')
    return jsonify(ok=True)
@app.post('/api/password')
@authenticated()
def change_password():
    data=body();old=data.get('oldPassword','');new=data.get('newPassword','')
    if not isinstance(old,str) or not isinstance(new,str) or not 8<=len(new)<=128:raise ApiError('Nové heslo musí mít 8–128 znaků.')
    rate_limit(['password:'+g.user['id']],5)
    if not password_ok(old,g.user['password_hash']):raise ApiError('Současné heslo není správné.',403)
    with db() as c:
        execute(c,'UPDATE users SET password_hash=%s WHERE id=%s',(password_hash(new),g.user['id']));execute(c,'DELETE FROM sessions WHERE user_id=%s AND token_hash<>%s',(g.user['id'],g.user['token_hash']));audit(c,g.user['id'],'password_changed','Změna hesla')
    return jsonify(ok=True)
@app.get('/healthz')
def health():
    with db() as c:execute(c,'SELECT 1')
    return jsonify(status='ok')
@app.get('/')
def index():return send_from_directory(WEB,'index.html')
@app.get('/app.js')
def javascript():return send_from_directory(WEB,'app.js')
@app.get('/inventory.js')
def inventory_script():return send_from_directory(WEB,'inventory.js')
@app.get('/scanner.js')
def scanner_script():return send_from_directory(WEB,'scanner.js')
@app.get('/auth.js')
def auth_script():return send_from_directory(WEB,'auth.js')
@app.get('/style.css')
def css():return send_from_directory(WEB,'style.css')
@app.get('/assets/<path:name>')
def assets(name):return send_from_directory(ROOT/'aplikace/assets',name)
@app.get('/favicon.ico')
def favicon():return '',204
if __name__=='__main__':app.run(host='0.0.0.0',port=int(os.environ.get('PORT','10000')))

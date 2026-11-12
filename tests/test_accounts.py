import os,sys,json,tempfile,importlib,time,concurrent.futures
from pathlib import Path
import pytest
os.environ['BAROMETR_TEST_DB']=str(Path(tempfile.mkdtemp())/'accounts.sqlite3')
os.environ['BAROMETR_TEST_HTTP']='1'
os.environ['ADMIN1_USERNAME']='AdminOne'
os.environ['ADMIN1_PASSWORD']='test-admin-one-password'
os.environ['ADMIN2_USERNAME']='AdminTwo'
os.environ['ADMIN2_PASSWORD']='test-admin-two-password'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from server.app import app,db,one,execute,PRODUCTS

def login(username='AdminOne',password='test-admin-one-password'):
 c=app.test_client();r=c.post('/api/login',json={'username':username,'password':password});assert r.status_code==200,r.json
 me=c.get('/api/me').json;return c,{'X-CSRF-Token':me['csrf']}
def invite(c,h,max_uses=1):
 r=c.post('/api/admin/invites',json={'label':'Test','maxUses':max_uses,'days':7},headers=h);assert r.status_code==200,r.json;return r.json

def test_session_and_privilege_enforcement():
 anonymous=app.test_client();assert anonymous.get('/api/catalog').status_code==401
 a,h=login();assert a.get('/api/me').json['user']['role']=='admin'
 assert a.post('/api/admin/invites',json={}).status_code==403
 assert a.post('/api/admin/invites',json={},headers={**h,'Origin':'https://evil.example'}).status_code==403
 code=invite(a,h)['code'];u=app.test_client()
 r=u.post('/api/register',json={'firstName':'Jan','lastName':'Novák','username':'tester_one','password':'safe-test-password','inviteCode':code,'role':'admin'})
 assert r.status_code==200,r.json
 me=u.get('/api/me').json;uh={'X-CSRF-Token':me['csrf']};assert me['user']['role']=='user'
 assert 'password_hash' not in json.dumps(me)
 assert u.get('/api/admin/users').status_code==403
 assert u.post('/api/admin/invites',json={},headers=uh).status_code==403
 p=next(iter(PRODUCTS))
 assert u.post('/api/unlocks',json={'productId':p},headers=uh).status_code==403
 assert u.get('/api/products/'+p).status_code==403
 assert u.put('/api/state',json={'ownerPreview':True,'rows':[{}],'records':[]},headers=uh).status_code==403
 assert u.post('/api/activity',json={'action':'catalog'},headers=uh).status_code==200
 assert u.post('/api/activity',json={'action':'steal','detail':'arbitrary'},headers=uh).status_code==400
 repeat=app.test_client().post('/api/register',json={'firstName':'Eva','lastName':'Nová','username':'tester_repeat','password':'safe-test-password','inviteCode':code});assert repeat.status_code==400
 user_id=me['user']['id'];d=a.get('/api/admin/users/'+user_id).json
 assert d['user']['login_count']==1 and any(e['action']=='view_catalog' for e in d['events'])
 assert a.post('/api/admin/users/'+user_id+'/status',json={'status':'suspended'},headers=h).status_code==200
 assert u.get('/api/me').status_code==401
 assert a.delete('/api/admin/users/'+user_id,json={'confirmation':'wrong'},headers=h).status_code==400
 assert a.delete('/api/admin/users/'+user_id,json={'confirmation':'tester_one'},headers=h).status_code==200
 assert a.get('/api/admin/users/'+user_id).status_code==404
 with db() as c:assert one(c,'SELECT COUNT(*) AS n FROM events WHERE user_id=%s',(user_id,))['n']==0
 assert a.delete('/api/admin/users/'+a.get('/api/me').json['user']['id'],json={'confirmation':'AdminOne'},headers=h).status_code==403

def test_invite_atomicity_and_rollback():
 a,h=login();data=invite(a,h)
 def registration(i):
  c=app.test_client();return c.post('/api/register',json={'firstName':'Tester','lastName':'Race','username':'race_'+str(i),'password':'safe-test-password','inviteCode':data['code']}).status_code
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(registration,[1,2]))
 assert sorted(results)==[200,400]
 with db() as c:assert one(c,'SELECT used_count FROM invitations WHERE id=%s',(data['id'],))['used_count']==1
 expired=invite(a,h)
 with db() as c:execute(c,'UPDATE invitations SET expires_at=%s WHERE id=%s',(time.time()-1,expired['id']))
 assert app.test_client().post('/api/register',json={'firstName':'A','lastName':'B','username':'expired_user','password':'safe-test-password','inviteCode':expired['code']}).status_code==400
 revoked=invite(a,h);assert a.post('/api/admin/invites/'+revoked['id']+'/revoke',json={},headers=h).status_code==200
 assert app.test_client().post('/api/register',json={'firstName':'A','lastName':'B','username':'revoked_user','password':'safe-test-password','inviteCode':revoked['code']}).status_code==400

def test_two_admins_and_shared_invites():
 a,h=login();b,bh=login('AdminTwo','test-admin-two-password');code=invite(a,h)
 assert any(i['id']==code['id'] for i in b.get('/api/admin/invites').json['invites'])
 assert b.post('/api/admin/invites/'+code['id']+'/revoke',json={},headers=bh).status_code==200
 p=next(iter(PRODUCTS));assert a.post('/api/unlocks',json={'productId':p},headers=h).status_code==200
 assert a.get('/api/products/'+p).status_code==200
 assert p not in b.get('/api/me').json['state']['unlocks']
 assert a.post('/api/logout',json={},headers=h).status_code==200;assert a.get('/api/me').status_code==401

def test_password_hash_and_rate_limit():
 with db() as c:
  u=one(c,'SELECT * FROM users WHERE username_key=%s',('adminone',));assert u['password_hash'].startswith('scrypt$');assert 'test-admin-one-password' not in u['password_hash']
 c=app.test_client()
 for i in range(5):assert c.post('/api/login',json={'username':'badaccount','password':'bad'}).status_code==401
 assert c.post('/api/login',json={'username':'badaccount','password':'bad'}).status_code==429

def test_password_change_revokes_other_sessions():
 a,h=login('AdminTwo','test-admin-two-password');b,bh=login('AdminTwo','test-admin-two-password')
 assert a.post('/api/password',json={'oldPassword':'test-admin-two-password','newPassword':'replacement-test-password'},headers=h).status_code==200
 assert b.get('/api/me').status_code==401
 assert a.get('/api/me').status_code==200
 assert a.post('/api/password',json={'oldPassword':'replacement-test-password','newPassword':'test-admin-two-password'},headers=h).status_code==200

def test_barcode_lookup_validation_and_fallback(monkeypatch):
 from io import BytesIO
 from urllib.error import URLError
 a,h=login()
 assert app.test_client().get('/api/barcode/3017620422003').status_code==401
 for code in ('abc','1234567','3017620422004','12345678901'):
  assert a.get('/api/barcode/'+code).status_code==400
 seen=[]
 def lookup(req,timeout):
  seen.append((req.full_url,timeout))
  return BytesIO(json.dumps({'status':1,'product':{'product_name':'Example spirit','quantity':'700 ml','brands':'Example'}}).encode())
 monkeypatch.setattr('urllib.request.urlopen',lookup)
 r=a.get('/api/barcode/3017620422003')
 assert r.status_code==200 and r.json['name']=='Example spirit' and r.json['quantity']=='700 ml'
 assert seen[0][0].startswith('https://world.openfoodfacts.org/api/v2/product/3017620422003.json?fields=') and seen[0][1]==7
 monkeypatch.setattr('urllib.request.urlopen',lambda *a,**kw:BytesIO(b'{"status":0}'))
 assert a.get('/api/barcode/3017620422003').json['found'] is False
 def offline(*args,**kwargs):raise URLError('offline')
 monkeypatch.setattr('urllib.request.urlopen',offline)
 assert a.get('/api/barcode/3017620422003').status_code==503
 assert a.get('/scanner.js').status_code==200

def test_inventory_plan_and_private_scan_photos():
 import base64
 a,h=login();b,bh=login('AdminTwo','test-admin-two-password')
 product_id=next(iter(PRODUCTS));product=PRODUCTS[product_id]
 assert a.post('/api/unlocks',json={'productId':product_id},headers=h).status_code==200
 entry={'id':'planned-1','productId':product_id,'capacity':product['variants'][0]['ml'],'label':'Police 1','status':'pending'}
 state={'rows':[],'records':[],'cycle':'Měsíční','closing':'04:00','inventoryPlan':{'entries':[entry],'runId':'test-run'}}
 assert a.put('/api/state',json=state,headers=h).status_code==200
 assert a.get('/api/me').json['state']['inventoryPlan']['entries'][0]['label']=='Police 1'
 duplicate={**state,'inventoryPlan':{'entries':[entry,entry]}}
 assert a.put('/api/state',json=duplicate,headers=h).status_code==400
 invalid={**state,'inventoryPlan':{'entries':[{**entry,'capacity':123}]}}
 assert a.put('/api/state',json=invalid,headers=h).status_code==400
 image='data:image/jpeg;base64,'+base64.b64encode(b'\xff\xd8test-jpeg\xff\xd9').decode()
 url='/api/scan-photos/test-private-snapshot'
 assert app.test_client().put(url,json={'image':image}).status_code==401
 assert a.put(url,json={'image':'not jpeg'},headers=h).status_code==400
 assert a.put(url,json={'image':image},headers=h).status_code==200
 assert a.put(url,json={'image':image},headers=h).status_code==200
 assert a.get(url).content_type=='image/jpeg'
 assert a.get(url).data==b'\xff\xd8test-jpeg\xff\xd9'
 replacement='data:image/jpeg;base64,'+base64.b64encode(b'\xff\xd8retry-jpeg\xff\xd9').decode()
 assert a.put(url,json={'image':replacement},headers=h).status_code==200
 assert a.get(url).data==b'\xff\xd8retry-jpeg\xff\xd9'
 assert b.get(url).status_code==404
 assert b.put(url,json={'image':image},headers=bh).status_code==404
 assert a.get('/inventory.js').status_code==200

def test_catalog_euro_prices():
 a,h=login();catalog=a.get('/api/catalog').json
 assert catalog['currency']=='EUR'
 prices=[p['unlockPrice'] for p in catalog['products']]
 assert min(prices)==0.49 and max(prices)==1.99
 assert all(p in (0.49,0.79,0.99,1.29,1.49,1.99) for p in prices)

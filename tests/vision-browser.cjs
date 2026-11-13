// Workflow test with a simulated camera and mocked AI. Not a real-world accuracy test.
const {chromium}=require('playwright'),assert=require('node:assert/strict');
const BASE=process.env.BAROMETR_BROWSER_URL||'http://127.0.0.1:10003';
assert(['127.0.0.1','localhost'].includes(new URL(BASE).hostname),'Use a disposable local server only');
(async()=>{
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']});
 const context=await browser.newContext({viewport:{width:390,height:844}});
 await context.addInitScript(()=>{window.testScene='bottle';Object.defineProperty(navigator.mediaDevices,'getUserMedia',{value:async()=>{const canvas=document.createElement('canvas');canvas.width=640;canvas.height=960;const ctx=canvas.getContext('2d');const draw=()=>{ctx.fillStyle='#c5c5c5';ctx.fillRect(0,0,640,960);if(window.testScene==='bottle'){ctx.fillStyle='#555';ctx.fillRect(235,180,170,620);ctx.fillRect(280,100,80,100);}};draw();const timer=setInterval(draw,100);const stream=canvas.captureStream(10);stream.getTracks()[0].addEventListener('ended',()=>clearInterval(timer));return stream;}});});
 const p=await context.newPage(),errors=[];p.on('pageerror',e=>errors.push(e.message));
 await p.goto(BASE);await p.locator('[name=username]').fill('BatchTest');await p.locator('[name=password]').fill('batch-test-local-only');await p.locator('#auth-form button[type=submit]').click();await p.locator('#mobile-nav').waitFor();
 const catalog=await p.evaluate(()=>BarometrAuth.api('/api/catalog')),products=catalog.products.slice(0,2);
 for(const product of products)await p.evaluate(id=>BarometrAuth.send('/api/unlocks',{productId:id}),product.id);
 await p.evaluate(products=>BarometrAuth.send('/api/state',{rows:[],records:[],cycle:'Měsíční',closing:'04:00',inventoryPlan:{runId:'test-auto-run',entries:products.map((p,i)=>({id:'auto-'+i,productId:p.id,capacity:p.variants[0].ml,label:'Test '+i,status:'pending'}))}},'PUT'),products);
 await p.reload();
 await p.route('**/api/vision/status',r=>r.fulfill({json:{configured:true,enabled:true,calibrated:false}}));
 let calls=0,readable=false;
 await p.route('**/api/vision/analyze',async r=>{calls++;const request=r.request().postDataJSON();assert.equal(request.images.length,2);assert(request.images.every(x=>x.startsWith('data:image/jpeg;base64,')&&x.length<180000));await r.fulfill({json:readable?{detected:true,ml:Math.round(request.capacity/20)*10,method:'vision-estimate',label:'Automatický AI odhad · neověřená přesnost',markers:{top:20,level:50,bottom:80},calibrated:false,evidence:'two-frame-consistency'}:{detected:false,reason:'Hladina není zřetelná — otočte lahev.'}});});
 await p.locator('#mobile-nav [data-start-scan]').click();await p.getByText('Hladina není zřetelná — otočte lahev.').waitFor();
 assert.equal(await p.locator('[data-marker]').count(),0,'No manual sliders in automatic mode');
 assert.equal((await p.evaluate(()=>BarometrAuth.api('/api/me'))).state.records.length,0);
 await p.waitForTimeout(1800);assert.equal(calls,1,'Unreadable frames must not cause repeated paid calls');
 readable=true;await p.locator('[data-scan=capture]').click();
 await p.waitForFunction(()=>document.querySelector('.scan-auto-status')?.textContent.includes('Odeberte předchozí'));
 let state=(await p.evaluate(()=>BarometrAuth.api('/api/me'))).state;assert.equal(state.records.length,1);assert.equal(state.records[0].measurement.method,'vision-estimate');
 await p.waitForTimeout(1800);assert.equal(calls,2,'Same bottle must not be saved for the next entry');
 await p.evaluate(()=>window.testScene='blank');await p.waitForTimeout(1000);await p.evaluate(()=>window.testScene='bottle');
 await p.waitForFunction(()=>!document.querySelector('.scanner'));state=(await p.evaluate(()=>BarometrAuth.api('/api/me'))).state;assert.equal(state.records.length,2);assert(state.inventoryPlan.entries.every(e=>e.status==='done'));assert.equal(calls,3);
 // Real disabled provider status must be visible and must not call analysis or save anything.
 await p.unroute('**/api/vision/status');await p.locator('#mobile-nav [data-start-scan]').click();await p.getByText(/AI není připojená nebo povolená/).waitFor();assert(await p.locator('[data-scan=capture]').isDisabled());assert.equal(calls,3);await p.screenshot({path:'/tmp/barometr-ai-not-configured.png'});await p.locator('[data-scan=close]').click();
 assert.deepEqual(errors,[]);await browser.close();console.log('AI workflow (mocked): no manual markers, unreadable rejection, bounded requests, automatic save/next, bottle-removal gate and disabled-provider status passed.');
})().catch(e=>{console.error(e);process.exit(1)});

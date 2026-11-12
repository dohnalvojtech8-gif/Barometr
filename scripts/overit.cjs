const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const root=path.resolve(__dirname,'..'),ctx={window:{}};
vm.runInNewContext(fs.readFileSync(path.join(root,'aplikace/catalog-data.js'),'utf8'),ctx);
const products=ctx.window.BAROMETR_CATALOG.products;
assert(products.length>=1000);
assert.equal(new Set(products.map(p=>p.id)).size,products.length);
for(const p of products){assert(p.name&&p.category&&p.variants.length);assert([0.49,0.79,0.99,1.29,1.49,1.99].includes(p.unlockPrice));assert.equal(new Set(p.variants.map(v=>v.ml)).size,p.variants.length);for(const v of p.variants){assert(v.ml>=40&&v.ml<=6000);assert(v.source.startsWith('https://'));assert(v.image===null||v.image.startsWith('https://')||fs.existsSync(path.join(root,'aplikace',v.image)));}}
const app=fs.readFileSync(path.join(root,'aplikace/app.js'),'utf8');new vm.Script(app);assert(!/function top\(/.test(app));assert(app.includes('credits()===0'));assert(app.includes('reason:state.ownerPreview'));
console.log(`PASS: ${products.length} products, unique IDs and volumes, valid sources, price bounds, JavaScript syntax and browser-name regression.`);

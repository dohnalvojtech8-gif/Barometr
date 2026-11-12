const fs=require('fs'),path=require('path');const root=path.resolve(__dirname,'..'),app=path.join(root,'aplikace');let html=fs.readFileSync(path.join(app,'index.html'),'utf8');
html=html.replace(/<script src="catalog-data\.js[^\"]*"><\/script>/,'<script>'+fs.readFileSync(path.join(app,'catalog-data.js'),'utf8').replace(/<\/script/gi,'<\\/script')+'</script>');
html=html.replace(/<script src="app\.js[^\"]*"><\/script>/,'<script>'+fs.readFileSync(path.join(app,'app.js'),'utf8').replace(/<\/script/gi,'<\\/script')+'</script>');
for(const file of ['amundsen.jpg','captain-morgan.png','jagermeister.png']){const mime=file.endsWith('.jpg')?'image/jpeg':'image/png';html=html.split('assets/'+file).join('data:'+mime+';base64,'+fs.readFileSync(path.join(app,'assets',file)).toString('base64'));}
fs.writeFileSync(path.join(root,'02-INTERAKTIVNI-APLIKACE.html'),html);console.log('Single-file application rebuilt. Supplier photographs require internet. Static 01 preview is the archived v0.2 design.');

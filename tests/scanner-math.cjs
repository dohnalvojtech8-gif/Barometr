const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const sandbox={window:{addEventListener(){}},document:{addEventListener(){}}};vm.runInNewContext(fs.readFileSync('server/web/scanner.js','utf8'),sandbox);
const {validCode,weightVolume}=sandbox.window.BarometrScanner;
assert(validCode('3017620422003'));assert(!validCode('3017620422004'));assert(!validCode('3017620422003foo'));
assert.equal(weightVolume(700,400,1100,750),350);assert.equal(weightVolume(700,400,1100,400),0);assert.equal(weightVolume(700,400,1100,1100),700);
for(const args of [[700,400,400,400],[700,400,1100,1200],[700,400,1100,399],[700,NaN,1100,700],[0,400,1100,700]])assert.throws(()=>weightVolume(...args));
console.log('Scanner: barcode checksum, mass calibration, empty/full boundaries and invalid inputs passed.');

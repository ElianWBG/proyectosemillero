const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const path=require('node:path');
function boot(saved,blocked=false){
 const picker={value:'',addEventListener(name,handler){this[name]=handler;}};
 const state={body:{dataset:{}},changed:0};
 const storage={getItem(){if(blocked)throw Error('blocked');return saved;},setItem(key,value){if(blocked)throw Error('blocked');saved=value;}};
 vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../static/theme.js'),'utf8'),{
  document:{body:state.body,getElementById:()=>picker},localStorage:storage,Event,
  window:{dispatchEvent(){state.changed++;}},
 });
 return {picker,state,saved:()=>saved};
}
test('la propuesta inicial es clara y minimalista',()=>assert.equal(boot(null).state.body.dataset.theme,'clean'));
test('el selector restaura la paleta original y recuerda la preferencia',()=>{
 const app=boot(null);app.picker.value='original';app.picker.change();
 assert.equal(app.state.body.dataset.theme,'original');assert.equal(app.saved(),'original');
 assert.equal(boot(app.saved()).picker.value,'original');
});
test('funciona con almacenamiento bloqueado y preferencias desconocidas',()=>{
 assert.equal(boot(null,true).picker.value,'clean');
 assert.equal(boot('invalid').picker.value,'clean');
});

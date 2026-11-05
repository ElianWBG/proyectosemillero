const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const path=require('node:path');

function setup(fetch=async()=>{throw Error('Unexpected request');}){
 const elements=new Map(),events={};
 const context=new Proxy({}, {get:()=>()=>{}});
 const element=id=>{
  if(!elements.has(id))elements.set(id,{value:'test',textContent:'',hidden:false,disabled:false,
   children:[],classList:{toggle(){}},setAttribute(){},removeAttribute(){},replaceChildren(){this.children=[];},append(...items){this.children.push(...items);},
   getContext:()=>context,addEventListener(name,handler){this[name]=handler;},reportValidity:()=>true});
  return elements.get(id);
 };
 const sandbox={console,AbortController,FormData,Blob,setTimeout,clearTimeout,performance,
  document:{cookie:'',getElementById:element,querySelectorAll:()=>[],createElement:()=>element(Symbol()),createTextNode:x=>x},
  navigator:{mediaDevices:{}},window:{isSecureContext:true,addEventListener:(name,handler)=>events[name]=handler},fetch};
 vm.createContext(sandbox);
 vm.runInContext(fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8'),sandbox);
 return {element,sandbox,run:code=>vm.runInContext(code,sandbox)};
}

test('cancelar una autorización pendiente libera la cámara cuando llega el permiso',async()=>{
 const app=setup();let resolvePermission,stopped=0;
 app.sandbox.navigator.mediaDevices.getUserMedia=()=>new Promise(resolve=>resolvePermission=resolve);
 const starting=app.element('config').submit({preventDefault(){}});
 assert.equal(app.element('stop').disabled,false);
 await app.run('stopSession(false)');
 resolvePermission({getTracks:()=>[{stop(){stopped++;}}]});
 await starting;
 assert.equal(stopped,1);
 assert.equal(app.run('active'),false);
 assert.equal(app.element('start').disabled,false);
});

test('una respuesta atrasada no cambia los resultados de la siguiente sesión',async()=>{
 let resolveFrame;
 const app=setup(()=>new Promise(resolve=>resolveFrame=resolve));
 app.run("generation=1;currentSession={id:'old'}");
 const sending=app.run('sendFrame(new Blob(),1)');
 app.run("generation=2;currentSession={id:'new'}");
 resolveFrame({ok:true,json:async()=>({id:'old',current:99})});
 await sending;
 assert.equal(app.run('currentSession.id'),'new');
 assert.notEqual(app.element('current').textContent,99);
});

test('un cierre fallido conserva el aviso y no confirma un guardado inexistente',async()=>{
 const app=setup(async()=>({ok:false,json:async()=>({error:'Sin conexión'})}));
 app.run("currentSession={id:'test',active:true};active=true");
 assert.equal(await app.run('stopSession()'),false);
 assert.match(app.element('notice').textContent,/no se pudo confirmar/);
 assert.equal(app.element('start').disabled,false);
});

test('cancelar un inicio pendiente impide reiniciar hasta resolver la creación',async()=>{
 const app=setup();let resolveStart;
 app.sandbox.waiting=new Promise(resolve=>resolveStart=resolve);
 app.run('pendingStart=waiting;preparing=true;busy=true');
 const stopping=app.run('stopSession(false)');
 assert.equal(app.element('start').disabled,true);
 resolveStart({id:'cancelled'});
 await stopping;
 assert.equal(app.element('start').disabled,false);
});

test('el historial conserva la respuesta más reciente aunque llegue primero',async()=>{
 const requests=[];
 const app=setup(()=>new Promise(resolve=>requests.push(resolve)));
 const first=app.run('loadHistory()'),second=app.run('loadHistory()');
 const session=title=>({title,started_at:'2026-11-05T12:00:00Z',mode:'Rostros',source:'Imagen',peak:2,frames:1,active:false,id:title});
 requests[1]({ok:true,json:async()=>({sessions:[session('reciente')]})});
 await second;
 requests[0]({ok:true,json:async()=>({sessions:[session('antigua')]})});
 await first;
 const rows=app.element('history-body').children;
 assert.equal(rows.length,1);
 assert.equal(rows[0].children[0].textContent,'reciente');
 assert.equal(app.element('refresh').disabled,false);
});

test('el historial permite reintentar después de un fallo',async()=>{
 const app=setup(async()=>({ok:false,json:async()=>({error:'PostgreSQL no disponible'})}));
 await app.run('loadHistory()');
 assert.match(app.element('history-message').textContent,/PostgreSQL/);
 assert.equal(app.element('history-message').hidden,false);
 assert.equal(app.element('refresh').disabled,false);
});


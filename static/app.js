"use strict";
const $=id=>document.getElementById(id);
let currentSession=null,stream=null,active=false,sequence=0,timer=null,started=0,busy=false,controller=null,points=[],generation=0,preparing=false,closing=null,pendingStart=null,historyRequest=0,sessionMode=null;
const csrf=()=>document.cookie.split('; ').find(x=>x.startsWith('csrftoken='))?.split('=')[1]||'';
function notice(message,success=false){
 // Restart the countdown even when another notice replaces the current one.
 $('notification').className='';
 void $('notification').offsetWidth;
 $('notice').textContent=message;$('notice').hidden=!message;
 $('notification').hidden=!message;
 $('notification').className='notification '+(success?'notification-success':'notification-warning');
 $('notification').setAttribute('role',success?'status':'alert');
 $('notification-title').textContent=success?'Notificación':'Atención';
 $('notification-icon').textContent=success?'✓':'!';
}
$('notification').addEventListener('animationend',event=>{
 if($('notification').hidden)return;
 if(event.animationName==='notification-countdown'){
  $('notification').className+=' notification-leaving';
 }else if(event.animationName==='notification-exit'&&$('notification').className.includes('notification-leaving')){
  notice('');
 }
});
$('notification-close').addEventListener('click',()=>notice(''));
window.addEventListener('keydown',event=>{if(event.key==='Escape')notice('');});
async function api(url,body=null,signal=null){
 const pending=new AbortController();let timedOut=false;
 const cancel=()=>pending.abort();
 if(signal?.aborted)pending.abort();else signal?.addEventListener('abort',cancel,{once:true});
 const deadline=setTimeout(()=>{timedOut=true;pending.abort();},15000);
 try{
  const options={credentials:'same-origin',signal:pending.signal,headers:{}};
  if(body!==null){options.method='POST';options.body=body;options.headers['X-CSRFToken']=csrf();}
  const response=await fetch(url,options);let data;
  try{data=await response.json();}catch(error){if(error.name==='AbortError')throw error;throw new Error('El servidor no devolvió una respuesta válida. Recarga la página e intenta de nuevo.');}
  if(!response.ok)throw new Error(data.error||'No se pudo completar la operación.');return data;
 }catch(error){
  if(timedOut)throw new Error('El servidor tardó demasiado en responder. Intenta nuevamente.');
  if(error instanceof TypeError)throw new Error('No se pudo conectar con el servidor. Revisa la conexión.');
  throw error;
 }finally{clearTimeout(deadline);signal?.removeEventListener('abort',cancel);}
}
function status(text,running=false){$('status').replaceChildren();const dot=document.createElement('span');dot.className='dot'+(running?'':' gray');$('status').append(dot,document.createTextNode(text));}
function controls(){
 $('start').disabled=active||busy||!!currentSession?.active;
 const pending=!!currentSession?.active;
 $('stop').disabled=!(active||preparing||pending)||busy||!!closing;
 $('cancel').disabled=!(active||preparing||pending)||!!closing;
 $('stop').textContent=currentSession?.source==='Imagen'?'Guardar imagen':'Detener y guardar';
 ['title','confidence','capacity','image-button'].forEach(id=>$(id).disabled=active||busy||!!currentSession?.active);
 $('mode').disabled=busy||!!closing;
 $('mode').setAttribute('aria-describedby','mode-help mode-lock');
 $('mode-lock').hidden=!currentSession?.active;
 $('mode-lock').textContent='Hay un resultado pendiente. Guarda o cancela antes de cambiar de modo.';
 $('config').setAttribute('aria-busy',String(busy));
}
function chart(){const canvas=$('chart'),ctx=canvas.getContext('2d');ctx.clearRect(0,0,900,110);const palette=typeof getComputedStyle==='function'?getComputedStyle(document.body):null;const line=palette?.getPropertyValue('--chart-line').trim()||'#348e70';ctx.strokeStyle=palette?.getPropertyValue('--chart-grid').trim()||'#eaf0ed';for(const y of [20,55,90]){ctx.beginPath();ctx.moveTo(20,y);ctx.lineTo(880,y);ctx.stroke();}if(!points.length)return;const max=Math.max(2,...points);ctx.strokeStyle=line;ctx.lineWidth=2.5;ctx.beginPath();points.forEach((n,i)=>{const x=20+i*860/59,y=90-n*70/max;i?ctx.lineTo(x,y):ctx.moveTo(x,y);});ctx.stroke();const last=points.length-1;ctx.beginPath();ctx.fillStyle=line;ctx.arc(20+last*860/59,90-points[last]*70/max,3.5,0,Math.PI*2);ctx.fill();}
function render(data){currentSession=data;$('current').textContent=data.current;$('peak').textContent=data.peak;$('frames').textContent=data.frames;$('limit-number').textContent=data.capacity;if(data.image){$('processed').src=data.image;$('processed').hidden=false;$('empty').hidden=true;$('latency').textContent=data.processing_ms+' ms';$('speed').textContent='Procesamiento: '+data.processing_ms+' ms';points.push(data.current);if(points.length>60)points.shift();chart();}$('current').classList.toggle('over',data.current>data.capacity);$('capacity-note').textContent=data.current>data.capacity?'Límite de referencia superado':'Dentro del límite de referencia';}
async function newSession(source,run){sessionMode=$('mode').value;const form=new FormData();form.set('title',$('title').value.trim());form.set('mode',$('mode').value);form.set('capacity',$('capacity').value);form.set('source',source);pendingStart=api('/api/sessions/',form);let data;try{data=await pendingStart;}finally{pendingStart=null;}if(run!==generation){try{const body=new FormData();body.set('discard','1');await api('/api/sessions/'+data.id+'/stop/',body);}catch{}return null;}$('processed').hidden=true;$('processed').removeAttribute('src');$('empty').hidden=false;$('latency').textContent='—';$('speed').textContent='Esperando fotograma';$('duration').textContent='00:00';sequence=0;points=[];chart();started=Date.now();render(data);$('session-state').textContent=data.title;$('source-label').textContent=source==='camera'?'CÁMARA DEL COMPUTADOR':'PRUEBA CON IMAGEN';$('screen-badge').textContent=source==='camera'?'EN DIRECTO':'IMAGEN DE PRUEBA';$('screen-badge').hidden=false;return data;}
function duration(){const t=Math.floor((Date.now()-started)/1000);$('duration').textContent=String(Math.floor(t/60)).padStart(2,'0')+':'+String(t%60).padStart(2,'0');}
async function sendFrame(blob,run,signal=null){
 const id=currentSession.id,body=new FormData();body.set('image',blob,'frame.jpg');body.set('sequence',String(++sequence));body.set('confidence',$('confidence').value||'0.85');
 const data=await api('/api/sessions/'+id+'/frame/',body,signal);
 if(run!==generation||currentSession?.id!==id)return;
 render(data);duration();return data;
}
async function tick(run){
 if(!active||run!==generation)return;
 const begin=performance.now(),pending=new AbortController();controller=pending;
 try{
  const video=$('camera'),canvas=$('capture'),scale=Math.min(1,640/video.videoWidth,480/video.videoHeight);
  canvas.width=Math.round(video.videoWidth*scale);canvas.height=Math.round(video.videoHeight*scale);
  if(!canvas.width||!canvas.height)throw new Error('La cámara no entrega video. Revisa la conexión.');
  canvas.getContext('2d').drawImage(video,0,0,canvas.width,canvas.height);
  const blob=await new Promise(resolve=>canvas.toBlob(resolve,'image/jpeg',0.82));
  if(!active||run!==generation)return;
  if(!blob)throw new Error('No se pudo capturar el fotograma.');
  await sendFrame(blob,run,pending.signal);
 }catch(error){if(run===generation&&active&&error.name!=='AbortError'){notice(error.message);await stopSession(false);}}
 finally{if(controller===pending)controller=null;if(active&&run===generation)timer=setTimeout(()=>tick(run),Math.max(0,250-(performance.now()-begin)));}
}
async function stopSession(showMessage=true,discard=false){
 if(closing)return closing;
 generation++;active=false;preparing=false;busy=true;clearTimeout(timer);controller?.abort();
 stream?.getTracks().forEach(track=>track.stop());stream=null;$('camera').srcObject=null;
 const session=currentSession;
 closing=(async()=>{
  let saved=true;
  if(pendingStart){try{await pendingStart;}catch{}}
  if(session?.active){try{const body=new FormData();if(discard)body.set('discard','1');const result=await api('/api/sessions/'+session.id+'/stop/',body);if(!discard)render(result);else currentSession=null;}
   catch(error){saved=false;notice('La captura se detuvo, pero no se pudo confirmar el cierre: '+error.message);}}
  if(discard&&saved){currentSession=null;$('processed').hidden=true;$('processed').removeAttribute('src');$('empty').hidden=false;points=[];chart();['current','peak','frames'].forEach(id=>$(id).textContent='0');$('current').classList.toggle('over',false);$('capacity-note').textContent='Sin resultado pendiente';$('latency').textContent='--';$('speed').textContent='Sin procesamiento activo';$('duration').textContent='00:00';$('session-state').textContent='Sin sesi\u00f3n activa';$('source-label').textContent='EN ESPERA';$('screen-badge').hidden=true;}
  status(discard&&saved?'Operaci\u00f3n cancelada':'Captura detenida');$('screen-badge').textContent='SESIÓN FINALIZADA';
  if(showMessage&&saved)notice(discard?'Resultado descartado. Puedes cambiar de modo o elegir otra imagen.':'Sesión guardada. Puedes descargar el CSV desde el historial.',true);
  return saved;
 })();
 controls();
 try{return await closing;}finally{closing=null;busy=false;controls();}
}
$('config').addEventListener('submit',async event=>{
 event.preventDefault();if(active||busy||currentSession?.active)return;
 const run=++generation;busy=true;preparing=true;controls();notice('');status('Preparando cámara');
 try{
  if(!window.isSecureContext||!navigator.mediaDevices?.getUserMedia)throw new Error('Abre la aplicación en localhost o mediante HTTPS para utilizar la cámara.');
  const captured=await navigator.mediaDevices.getUserMedia({video:{width:{ideal:640},height:{ideal:480}},audio:false});
  if(run!==generation){captured.getTracks().forEach(track=>track.stop());return;}
  stream=captured;$('camera').srcObject=stream;await $('camera').play();
  if(run!==generation)return;
  if(!await newSession('camera',run)||run!==generation)return;
  active=true;preparing=false;
  stream.getVideoTracks().forEach(track=>track.addEventListener('ended',()=>{if(active&&run===generation){notice('La cámara se desconectó.');void stopSession(false);}}));
  status('Cámara activa',true);void tick(run);
 }catch(error){if(run===generation){
  const messages={NotAllowedError:'No se autorizó el acceso a la cámara. Habilita el permiso del navegador y vuelve a intentar.',NotFoundError:'No se encontró una cámara conectada.',NotReadableError:'Otra aplicación está utilizando la cámara. Ciérrala y vuelve a intentar.'};
  notice(messages[error.name]||error.message);await stopSession(false);
 }}finally{if(run===generation){busy=false;preparing=false;controls();}}
});
$('stop').addEventListener('click',()=>stopSession());
$('cancel').addEventListener('click',()=>stopSession(true,true));
$('image-button').addEventListener('click',()=>{if(!busy&&!active&&!currentSession?.active)$('image-file').click();});
$('image-file').addEventListener('change',async()=>{
 const file=$('image-file').files[0];$('image-file').value='';if(!file||busy||active||currentSession?.active)return;
 if(file.size>2*1024*1024){notice('La imagen supera 2 MB.');return;}
 if(!$('config').reportValidity())return;
 const run=++generation,pending=new AbortController();controller=pending;busy=true;preparing=true;controls();notice('');status('Procesando imagen');
 try{
  if(!await newSession('image',run)||run!==generation)return;
  await sendFrame(file,run,pending.signal);if(run!==generation)return;
  preparing=false;status('Imagen pendiente de guardar');notice('Revisa el resultado. Guarda o cancela antes de cambiar el modo o analizar otra imagen.',true);
 }catch(error){if(run===generation){notice(error.message);await stopSession(false,true);}}
 finally{if(controller===pending)controller=null;if(run===generation){busy=false;preparing=false;controls();}}
});
$('mode').addEventListener('change',()=>{
 if(currentSession?.active||busy||preparing||closing){
  if(sessionMode)$('mode').value=sessionMode;
  notice('No puedes cambiar de modo con un resultado pendiente. Pulsa Guardar imagen o Cancelar y descartar primero.');
  return;
 }
 if(currentSession){currentSession=null;$('processed').hidden=true;$('processed').removeAttribute('src');$('empty').hidden=false;points=[];chart();['current','peak','frames'].forEach(id=>$(id).textContent='0');$('screen-badge').hidden=true;$('session-state').textContent='Selecciona una imagen para analizar con el nuevo modo';$('source-label').textContent='EN ESPERA';$('latency').textContent='—';$('speed').textContent='Sin procesamiento activo';$('duration').textContent='00:00';$('current').classList.toggle('over',false);$('capacity-note').textContent='Sin resultado';status('Modo seleccionado');}
 notice('Modo cambiado. Selecciona una imagen para ejecutar una nueva detección.',true);
 $('mode-help').textContent={faces:'Mantén los rostros de frente y con buena iluminación.',bodies:'Encuadra a las personas de cuerpo completo; evita obstáculos.',mixed:'Combina ambos detectores. Puede requerir más tiempo por fotograma.'}[$('mode').value];controls();
});
$('capacity').addEventListener('input',()=>{if(!active&&!currentSession?.active)$('limit-number').textContent=$('capacity').value||'—';});
async function loadHistory(){const request=++historyRequest,msg=$('history-message');msg.hidden=true;$('refresh').disabled=true;try{const data=await api('/api/history/');if(request!==historyRequest)return;$('history-body').replaceChildren();$('history-empty').hidden=data.sessions.length>0;for(const s of data.sessions){const row=document.createElement('tr');for(const value of [s.title,new Date(s.started_at).toLocaleString('es-EC'),s.mode+' / '+s.source,s.peak,s.frames,s.active?'En curso':'Finalizada']){const cell=document.createElement('td');cell.textContent=String(value);row.append(cell);}const cell=document.createElement('td'),link=document.createElement('a');link.href='/api/sessions/'+s.id+'/export/';link.textContent='CSV ↗';link.setAttribute('aria-label','Descargar CSV de '+s.title);cell.append(link);row.append(cell);$('history-body').append(row);}}catch(error){if(request===historyRequest){msg.textContent=error.message;notice(error.message);}}finally{if(request===historyRequest)$('refresh').disabled=false;}}
document.querySelectorAll('[data-panel]').forEach(button=>button.addEventListener('click',()=>{document.querySelectorAll('.panel').forEach(p=>p.hidden=p.id!==button.dataset.panel);document.querySelectorAll('[data-panel]').forEach(b=>b.classList.toggle('active',b===button));if(button.dataset.panel==='history')loadHistory();}));
$('refresh').addEventListener('click',loadHistory);
window.addEventListener('pagehide',()=>{generation++;active=false;clearTimeout(timer);controller?.abort();stream?.getTracks().forEach(t=>t.stop());if(currentSession?.active){const body=new FormData();body.set('csrfmiddlewaretoken',csrf());if(currentSession.source==='Imagen')body.set('discard','1');navigator.sendBeacon('/api/sessions/'+currentSession.id+'/stop/',body);}});
window.addEventListener('themechange',chart);
chart();
controls();

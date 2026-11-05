import base64,csv,time
import cv2
from datetime import timedelta
from functools import wraps
from django.db import transaction,DatabaseError
from django.http import JsonResponse,HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET,require_POST
from .models import CountSession,CountSample
from .tracking import update_tracks
from .vision import decode_frame,detect_people,annotate,MAX_UPLOAD
def database_errors(view):
    @wraps(view)
    def wrapped(*args,**kwargs):
        try:return view(*args,**kwargs)
        except DatabaseError:return JsonResponse({'error':'No se pudo conectar con PostgreSQL. Revise su configuración y vuelva a intentar.'},status=503)
    return wrapped
def browser_key(request):
    if not request.session.session_key:request.session.create()
    return request.session.session_key
def serialized(s):
    return {'id':str(s.pk),'title':s.title,'mode':s.get_mode_display(),'source':s.get_source_display(),'capacity':s.capacity,'started_at':s.started_at.isoformat(),'ended_at':s.ended_at.isoformat() if s.ended_at else None,'frames':s.frame_count,'current':s.current_count,'peak':s.peak_count,'active':s.ended_at is None,'tracks':max(0,s.state.get('next_id',1)-1)}
@require_GET
@ensure_csrf_cookie
def index(request):return render(request,'index.html')
@require_POST
@database_errors
def start(request):
    title=request.POST.get('title','').strip();mode=request.POST.get('mode','faces');source=request.POST.get('source','camera')
    try:capacity=int(request.POST.get('capacity','20'))
    except ValueError:return JsonResponse({'error':'El límite debe ser un número entero.'},status=400)
    if not title or len(title)>80 or mode not in dict(CountSession.MODES) or source not in ('camera','image') or not 1<=capacity<=500:
        return JsonResponse({'error':'Indique un nombre de hasta 80 caracteres, modo válido y límite entre 1 y 500.'},status=400)
    key=browser_key(request)
    with transaction.atomic():
        # Un bloqueo sobre la sesión del navegador serializa inicios concurrentes.
        from django.contrib.sessions.models import Session
        Session.objects.select_for_update().get(session_key=key)
        CountSession.objects.filter(browser_key=key,ended_at__isnull=True).update(ended_at=timezone.now())
        s=CountSession.objects.create(browser_key=key,title=title,mode=mode,source=source,capacity=capacity)
    return JsonResponse(serialized(s),status=201)
@require_POST
@database_errors
def frame(request,pk):
    key=request.session.session_key
    s=CountSession.objects.filter(pk=pk,browser_key=key).first() if key else None
    if s is None:return JsonResponse({'error':'Sesión no encontrada.'},status=404)
    if s.ended_at:return JsonResponse({'error':'Esta sesión ya está cerrada.'},status=409)
    try:sequence=int(request.POST.get('sequence','0'))
    except ValueError:return JsonResponse({'error':'Secuencia no válida.'},status=400)
    if not 1<=sequence<=2147483647:return JsonResponse({'error':'La secuencia debe estar entre 1 y 2147483647.'},status=400)
    upload=request.FILES.get('image')
    if upload is None:return JsonResponse({'error':'Falta el fotograma.'},status=400)
    if upload.size>MAX_UPLOAD:return JsonResponse({'error':'La imagen supera 2 MB.'},status=413)
    begin=time.perf_counter()
    try:
        image=decode_frame(upload.read());boxes=detect_people(image,s.mode)
    except ValueError as error:return JsonResponse({'error':str(error)},status=400)
    except (cv2.error,RuntimeError):return JsonResponse({'error':'No se pudo ejecutar el detector. Revise el modelo y la instalación de OpenCV.'},status=503)
    now=timezone.now()
    with transaction.atomic():
        s=CountSession.objects.select_for_update().get(pk=s.pk)
        if s.ended_at or sequence<=s.sequence:return JsonResponse({'error':'Sesión cerrada o fotograma ya procesado.'},status=409)
        identifiers,state=update_tracks(boxes,s.state,now.timestamp(),max_distance=max(35,image.shape[1]*0.15))
        try:output=annotate(image,boxes,identifiers,s.capacity)
        except (cv2.error,RuntimeError):
            return JsonResponse({'error':'No se pudo preparar la imagen de resultado. Intente nuevamente.'},status=503)
        ms=round((time.perf_counter()-begin)*1000)
        changed=len(boxes)!=s.current_count
        last_saved=s.state.get('last_saved',0)
        save_sample=changed or not s.frame_count or now.timestamp()-last_saved>=2
        state['last_saved']=now.timestamp() if save_sample else last_saved
        s.current_count=len(boxes);s.peak_count=max(s.peak_count,len(boxes));s.frame_count+=1;s.sequence=sequence;s.state=state
        s.save(update_fields=['current_count','peak_count','frame_count','sequence','state'])
        if save_sample:CountSample.objects.create(session=s,count=len(boxes),processing_ms=ms)
    response=serialized(s)
    response.update({'image':'data:image/jpeg;base64,'+base64.b64encode(output).decode(),'processing_ms':ms,'ids':identifiers,'over_capacity':len(boxes)>s.capacity})
    return JsonResponse(response)
@require_POST
@database_errors
def stop(request,pk):
    key=request.session.session_key
    with transaction.atomic():
        s=CountSession.objects.select_for_update().filter(pk=pk,browser_key=key).first() if key else None
        if s is None:return JsonResponse({'error':'Sesión no encontrada.'},status=404)
        if s.ended_at is None:s.ended_at=timezone.now();s.save(update_fields=['ended_at'])
    return JsonResponse(serialized(s))
@require_GET
@database_errors
def history(request):
    key=request.session.session_key
    sessions=CountSession.objects.filter(browser_key=key)[:100] if key else []
    return JsonResponse({'sessions':[serialized(s) for s in sessions]})
@require_GET
@database_errors
def export_csv(request,pk):
    key=request.session.session_key
    s=CountSession.objects.filter(pk=pk,browser_key=key).first() if key else None
    if s is None:return JsonResponse({'error':'Sesión no encontrada.'},status=404)
    response=HttpResponse(content_type='text/csv; charset=utf-8');response['Content-Disposition']=f'attachment; filename="visorlab-{s.pk}.csv"'
    response.write('\ufeff');writer=csv.writer(response)
    writer.writerow(['sesion','fecha_iso','personas_visibles','procesamiento_ms','modo','origen'])
    for sample in s.samples.iterator():writer.writerow([str(s.pk),sample.recorded_at.isoformat(),sample.count,sample.processing_ms,s.mode,s.source])
    return response

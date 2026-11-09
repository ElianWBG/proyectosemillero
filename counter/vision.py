"""Procesamiento OpenCV independiente de Django y de la captura del navegador."""
from functools import lru_cache
from pathlib import Path
from threading import Lock
import io
import cv2
import numpy as np
from .body_detection import detect_bodies
from PIL import Image,UnidentifiedImageError
LOCK=Lock()
MAX_UPLOAD=2*1024*1024
def decode_frame(content,max_width=640,max_height=480):
    if not content or len(content)>MAX_UPLOAD:raise ValueError('La imagen debe ocupar entre 1 byte y 2 MB.')
    try:
        with Image.open(io.BytesIO(content)) as image:
            if image.format not in ('JPEG','PNG'):raise ValueError('Use una imagen JPEG o PNG.')
            w,h=image.size
            if min(w,h)<64 or w*h>3_000_000:raise ValueError('Use una imagen de al menos 64 px y hasta 3 megapíxeles.')
            image.verify()
    except (UnidentifiedImageError,OSError,Image.DecompressionBombError) as error:
        raise ValueError('El archivo no contiene una imagen válida.') from error
    frame=cv2.imdecode(np.frombuffer(content,np.uint8),cv2.IMREAD_COLOR)
    if frame is None:raise ValueError('No se pudo decodificar la imagen.')
    scale=min(1.0,max_width/frame.shape[1],max_height/frame.shape[0])
    if scale<1:frame=cv2.resize(frame,None,fx=scale,fy=scale,interpolation=cv2.INTER_AREA)
    return frame
@lru_cache(maxsize=1)
def detectors():
    model=Path(__file__).parent/'assets'/'face_detection_yunet_2023mar.onnx'
    if not model.exists():raise RuntimeError('Falta el modelo YuNet incluido con el proyecto.')
    face=cv2.FaceDetectorYN.create(str(model),'',(320,320),score_threshold=0.85,nms_threshold=0.3,top_k=5000)
    return face,None
def iou(a,b):
    ax,ay,aw,ah=a;bx,by,bw,bh=b
    area=max(0,min(ax+aw,bx+bw)-max(ax,bx))*max(0,min(ay+ah,by+bh)-max(ay,by))
    return area/(aw*ah+bw*bh-area) if area else 0
def suppress(boxes,threshold=0.35):
    result=[]
    for box in sorted(boxes,key=lambda b:b[2]*b[3],reverse=True):
        if all(iou(box,other)<threshold for other in result):result.append(box)
    return result
def fuse(faces,bodies):
    result=list(bodies)
    for x,y,w,h in faces:
        cx,cy=x+w/2,y+h/2
        if not any(bx<=cx<=bx+bw and by<=cy<=by+bh for bx,by,bw,bh in bodies):result.append((x,y,w,h))
    return suppress(result)
def detect_people(frame,mode,confidence=0.85,body_threshold=0.35):
    if mode not in ('faces','bodies','mixed'):raise ValueError('Modo de detección no válido.')
    if not 0.5<=confidence<=0.95:raise ValueError('La confianza debe estar entre 0.50 y 0.95.')
    if not 0.1<=body_threshold<=0.95:raise ValueError('La confianza de cuerpos debe estar entre 0.10 y 0.95.')
    face=detectors()[0] if mode in ('faces','mixed') else None
    faces=[];bodies=[]
    # Los modelos son compartidos; un candado evita inferencias concurrentes sobre ellos.
    with LOCK:
        if mode in ('faces','mixed'):
            face.setScoreThreshold(confidence)
            face.setInputSize((frame.shape[1],frame.shape[0]))
            _,detections=face.detect(frame)
            if detections is not None:
                for detection in detections:
                    x,y,w,h=map(int,detection[:4])
                    right=min(x+w,frame.shape[1]);bottom=min(y+h,frame.shape[0])
                    x=max(0,x);y=max(0,y);w=right-x;h=bottom-y
                    if w>=20 and h>=20:faces.append((x,y,w,h))
        if mode in ('bodies','mixed'):
            bodies=detect_bodies(frame,body_threshold)
    if mode=='faces':return suppress(faces)
    if mode=='bodies':return bodies
    return fuse(faces,bodies)
def annotate(frame,boxes,identifiers,capacity):
    image=frame.copy()
    for (x,y,w,h),identifier in zip(boxes,identifiers):
        cv2.rectangle(image,(x,y),(x+w,y+h),(88,220,165),2)
        cv2.putText(image,f'Persona #{identifier:03}',(x,max(20,y-8)),cv2.FONT_HERSHEY_SIMPLEX,0.55,(88,220,165),2)
    over=len(boxes)>capacity
    cv2.rectangle(image,(0,0),(image.shape[1],36),(24,36,49),-1)
    cv2.putText(image,f'VISIBLES: {len(boxes)} | LIMITE: {capacity}'+(' | LIMITE SUPERADO' if over else ''),(10,24),cv2.FONT_HERSHEY_SIMPLEX,0.52,(100,160,255) if over else (230,245,240),1)
    success,data=cv2.imencode('.jpg',image,[cv2.IMWRITE_JPEG_QUALITY,80])
    if not success:raise RuntimeError('No se pudo preparar el fotograma de salida.')
    return data.tobytes()

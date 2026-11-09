"""Person-class YOLOX inference with OpenCV DNN (COCO class 0).

Model and preprocessing specification: OpenCV Zoo object_detection_yolox.
Coordinates are decoded from stride grids and mapped back from a padded RGB image.
"""
from functools import lru_cache
from pathlib import Path
import cv2
import numpy as np


@lru_cache(maxsize=1)
def body_net():
    path=Path(__file__).parent/'assets'/'object_detection_yolox_2022nov.onnx'
    if not path.exists():
        raise RuntimeError('Falta el modelo YOLOX incluido para detectar personas.')
    return cv2.dnn.readNetFromONNX(str(path))


def decode_people(predictions,ratio,width,height,threshold):
    rows=np.asarray(predictions).reshape(-1,85).copy()
    grids=[];strides=[]
    for stride in (8,16,32):
        side=640//stride
        y,x=np.indices((side,side))
        grids.append(np.column_stack((x.ravel(),y.ravel())))
        strides.append(np.full((side*side,1),stride))
    grid=np.concatenate(grids);scale=np.concatenate(strides)
    if len(rows)!=len(grid):raise RuntimeError('Salida inesperada del detector de personas.')
    scores=rows[:,4]*rows[:,5]
    # Only retain candidates whose most likely COCO class is person.
    selected=(scores>=threshold)&(rows[:,5:].argmax(axis=1)==0)
    centers=(rows[selected,:2]+grid[selected])*scale[selected]
    sizes=np.exp(np.clip(rows[selected,2:4],-20,20))*scale[selected]
    corners=(centers-sizes/2)/ratio
    ends=(centers+sizes/2)/ratio
    boxes=[];weights=[]
    for start,end,score in zip(corners,ends,scores[selected]):
        x,y=np.clip(start,[0,0],[width,height]).astype(int)
        right,bottom=np.clip(end,[0,0],[width,height]).astype(int)
        if right>x and bottom>y:
            boxes.append([int(x),int(y),int(right-x),int(bottom-y)])
            weights.append(float(score))
    keep=cv2.dnn.NMSBoxes(boxes,weights,threshold,0.45)
    return [tuple(boxes[int(i)]) for i in np.asarray(keep).reshape(-1)]


def detect_bodies(frame,threshold):
    height,width=frame.shape[:2]
    ratio=min(640/width,640/height)
    resized=cv2.resize(frame,(max(1,int(width*ratio)),max(1,int(height*ratio))))
    padded=np.full((640,640,3),114,dtype=np.uint8)
    padded[:resized.shape[0],:resized.shape[1]]=resized
    net=body_net()
    net.setInput(cv2.dnn.blobFromImage(padded,swapRB=True))
    return decode_people(net.forward(),ratio,width,height,threshold)

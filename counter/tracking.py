"""Seguimiento por centroides. Identidad temporal, sin reconocimiento biométrico."""
from math import hypot
def update_tracks(boxes,state,now,max_distance=95,max_missed=5):
    tracks={k:dict(v) for k,v in state.get('tracks',{}).items() if now-v.get('seen',0)<3.0}
    centers=[(x+w/2,y+h/2) for x,y,w,h in boxes]
    candidates=sorted((hypot(t['x']-x,t['y']-y),key,i) for key,t in tracks.items() for i,(x,y) in enumerate(centers))
    used_tracks=set(); used_detections=set(); identifiers=[None]*len(boxes)
    for distance,key,i in candidates:
        if distance<=max_distance and key not in used_tracks and i not in used_detections:
            x,y=centers[i];tracks[key]={'x':x,'y':y,'seen':now,'missed':0}
            used_tracks.add(key);used_detections.add(i);identifiers[i]=int(key)
    for key in list(tracks):
        if key not in used_tracks:
            tracks[key]['missed']=tracks[key].get('missed',0)+1
            if tracks[key]['missed']>max_missed:del tracks[key]
    next_id=state.get('next_id',1)
    for i,(x,y) in enumerate(centers):
        if i not in used_detections:
            key=str(next_id);identifiers[i]=next_id;next_id+=1
            tracks[key]={'x':x,'y':y,'seen':now,'missed':0}
    return identifiers,{'tracks':tracks,'next_id':next_id}

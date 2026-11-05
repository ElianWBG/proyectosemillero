import uuid
from django.db import models
class CountSession(models.Model):
    MODES=[('faces','Rostros'),('bodies','Cuerpos completos'),('mixed','Mixto')]
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    browser_key=models.CharField(max_length=40,db_index=True)
    title=models.CharField(max_length=80)
    mode=models.CharField(max_length=8,choices=MODES,default='faces')
    source=models.CharField(max_length=8,choices=[('camera','Cámara'),('image','Imagen')],default='camera')
    capacity=models.PositiveSmallIntegerField(default=20)
    started_at=models.DateTimeField(auto_now_add=True,db_index=True)
    ended_at=models.DateTimeField(null=True,blank=True)
    frame_count=models.PositiveIntegerField(default=0)
    current_count=models.PositiveIntegerField(default=0)
    peak_count=models.PositiveIntegerField(default=0)
    sequence=models.PositiveIntegerField(default=0)
    state=models.JSONField(default=dict,blank=True)
    class Meta:
        ordering=['-started_at']
class CountSample(models.Model):
    session=models.ForeignKey(CountSession,on_delete=models.CASCADE,related_name='samples')
    recorded_at=models.DateTimeField(auto_now_add=True)
    count=models.PositiveIntegerField()
    processing_ms=models.PositiveIntegerField()
    class Meta:
        ordering=['recorded_at','id']
        indexes=[models.Index(fields=['session','recorded_at'],name='counter_session_time_idx')]

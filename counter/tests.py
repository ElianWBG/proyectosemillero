"""Pruebas con PostgreSQL real. Ejecutar python manage.py test counter."""
import io
from unittest.mock import patch,MagicMock
import cv2
import numpy as np
from PIL import Image
from django.test import TestCase,SimpleTestCase,Client
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import CountSession,CountSample
from .tracking import update_tracks
from .vision import decode_frame,detect_people,fuse,suppress

def blank():
    ok,data=cv2.imencode('.jpg',np.full((240,320,3),240,dtype=np.uint8))
    assert ok
    return data.tobytes()
def file(content=None):return SimpleUploadedFile('frame.jpg',content or blank(),content_type='image/jpeg')

class TrackingTests(SimpleTestCase):
    def test_same_person_keeps_identifier(self):
        ids,state=update_tracks([(10,10,30,30)],{},100)
        next_ids,_=update_tracks([(15,15,30,30)],state,100.25)
        self.assertEqual(ids,next_ids)
    def test_two_nearby_people_are_not_one(self):
        ids,_=update_tracks([(10,10,30,30),(45,10,30,30)],{},100)
        self.assertEqual(len(set(ids)),2)
    def test_only_visible_detections_count(self):
        _,state=update_tracks([(10,10,30,30)],{},100)
        ids,_=update_tracks([],state,100.5)
        self.assertEqual(ids,[])
    def test_old_track_expires(self):
        _,state=update_tracks([(10,10,30,30)],{},100)
        ids,_=update_tracks([(10,10,30,30)],state,104)
        self.assertEqual(ids,[2])
    def test_one_track_cannot_match_two_detections(self):
        _,state=update_tracks([(10,10,30,30)],{},100)
        ids,_=update_tracks([(10,10,30,30),(15,10,30,30)],state,100.25)
        self.assertEqual(len(set(ids)),2)
    def test_face_in_body_does_not_double_count(self):
        self.assertEqual(len(fuse([(35,10,20,20)],[(10,0,80,180)])),1)
    def test_nms_removes_duplicate_box(self):
        self.assertEqual(len(suppress([(10,10,100,100),(12,12,100,100)])),1)

class VisionTests(SimpleTestCase):
    def test_real_opencv_blank_has_no_faces(self):self.assertEqual(detect_people(decode_frame(blank()),'faces'),[])
    def test_real_opencv_blank_has_no_bodies(self):self.assertEqual(detect_people(decode_frame(blank()),'bodies'),[])
    def test_decode_rejects_non_image(self):
        with self.assertRaises(ValueError):decode_frame(b'not an image')
    def test_decode_rejects_size(self):
        with self.assertRaises(ValueError):decode_frame(b'a'*(2*1024*1024+1))
    def test_resizes_large_input(self):
        output=io.BytesIO();Image.new('RGB',(1600,900),'white').save(output,format='PNG')
        self.assertEqual(decode_frame(output.getvalue()).shape[:2],(360,640))
    def test_invalid_mode(self):
        with self.assertRaises(ValueError):detect_people(decode_frame(blank()),'invalid')
    def test_face_crossing_image_edge_is_clipped_correctly(self):
        detector=MagicMock()
        detector.detect.return_value=(None,np.array([[-15,-10,50,45]],dtype=np.float32))
        with patch('counter.vision.detectors',return_value=(detector,None)):
            self.assertEqual(detect_people(np.zeros((100,100,3),np.uint8),'faces'),[(0,0,35,35)])
    def test_face_outside_image_is_ignored(self):
        detector=MagicMock()
        detector.detect.return_value=(None,np.array([[110,10,40,40]],dtype=np.float32))
        with patch('counter.vision.detectors',return_value=(detector,None)):
            self.assertEqual(detect_people(np.zeros((100,100,3),np.uint8),'faces'),[])

class APITests(TestCase):
    def new(self,client=None,**kwargs):
        client=client or self.client
        return client.post('/api/sessions/',{'title':'Laboratorio P','mode':'faces','source':'image','capacity':2,**kwargs})
    def frame(self,session_id,sequence=1,client=None,content=None):
        return (client or self.client).post(f'/api/sessions/{session_id}/frame/',{'sequence':sequence,'image':file(content)})
    def test_home_and_static_references(self):
        response=self.client.get('/')
        self.assertContains(response,'Personas a la vista.')
        self.assertIn('csrftoken',response.cookies)
    def test_post_requires_csrf(self):
        client=Client(enforce_csrf_checks=True)
        self.assertEqual(self.new(client).status_code,403)
    def test_create_valid_and_postgresql(self):
        from django.db import connection
        self.assertEqual(connection.vendor,'postgresql')
        response=self.new();self.assertEqual(response.status_code,201)
        self.assertEqual(CountSession.objects.count(),1)
    def test_invalid_capacity(self):self.assertEqual(self.new(capacity=0).status_code,400)
    def test_invalid_mode(self):self.assertEqual(self.new(mode='other').status_code,400)
    def test_missing_title(self):self.assertEqual(self.new(title=' ').status_code,400)
    def test_frame_persists_count_and_peak(self):
        pk=self.new().json()['id']
        with patch('counter.views.detect_people',return_value=[(10,50,50,60),(100,50,50,60)]):
            response=self.frame(pk)
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['current'],2)
        self.assertTrue(response.json()['image'].startswith('data:image/jpeg;base64,'))
        with patch('counter.views.detect_people',return_value=[]):self.frame(pk,2)
        s=CountSession.objects.get(pk=pk);self.assertEqual((s.current_count,s.peak_count,s.frame_count),(0,2,2))
        self.assertEqual(CountSample.objects.filter(session=s).count(),2)
    def test_capacity_alert(self):
        pk=self.new(capacity=1).json()['id']
        with patch('counter.views.detect_people',return_value=[(10,50,50,60),(100,50,50,60)]):r=self.frame(pk)
        self.assertTrue(r.json()['over_capacity'])
    def test_duplicate_frame_is_rejected(self):
        pk=self.new().json()['id'];self.assertEqual(self.frame(pk).status_code,200)
        self.assertEqual(self.frame(pk).status_code,409)
        self.assertEqual(CountSession.objects.get(pk=pk).frame_count,1)
    def test_missing_frame(self):
        pk=self.new().json()['id']
        self.assertEqual(self.client.post(f'/api/sessions/{pk}/frame/',{'sequence':1}).status_code,400)
    def test_sequence_overflow_is_invalid_input(self):
        pk=self.new().json()['id']
        self.assertEqual(self.frame(pk,2147483648).status_code,400)
        self.assertEqual(CountSession.objects.get(pk=pk).frame_count,0)
    def test_encoding_failure_does_not_save_partial_counts(self):
        pk=self.new().json()['id']
        with patch('counter.views.annotate',side_effect=RuntimeError('encoder')):
            self.assertEqual(self.frame(pk).status_code,503)
        session=CountSession.objects.get(pk=pk)
        self.assertEqual(session.frame_count,0)
        self.assertEqual(session.samples.count(),0)
    def test_bad_image(self):
        pk=self.new().json()['id'];self.assertEqual(self.frame(pk,content=b'bad').status_code,400)
    def test_close_is_idempotent_and_disallows_frames(self):
        pk=self.new().json()['id'];url=f'/api/sessions/{pk}/stop/'
        self.assertEqual(self.client.post(url).status_code,200)
        self.assertEqual(self.client.post(url).status_code,200)
        self.assertEqual(self.frame(pk).status_code,409)
    def test_start_closes_previous_browser_session(self):
        first=self.new().json()['id'];self.new()
        self.assertIsNotNone(CountSession.objects.get(pk=first).ended_at)
    def test_another_browser_cannot_read_or_change(self):
        pk=self.new().json()['id'];other=Client()
        self.assertEqual(self.frame(pk,client=other).status_code,404)
        self.assertEqual(other.post(f'/api/sessions/{pk}/stop/').status_code,404)
        self.assertEqual(other.get(f'/api/sessions/{pk}/export/').status_code,404)
        self.assertEqual(other.get('/api/history/').json()['sessions'],[])
    def test_real_blank_opencv_api_roundtrip(self):
        pk=self.new().json()['id'];response=self.frame(pk)
        self.assertEqual(response.status_code,200);self.assertEqual(response.json()['current'],0)
    def test_csv_exports_saved_samples(self):
        pk=self.new().json()['id'];self.frame(pk)
        response=self.client.get(f'/api/sessions/{pk}/export/')
        self.assertEqual(response.status_code,200);self.assertIn('personas_visibles',response.content.decode('utf-8-sig'))
        self.assertEqual(len(response.content.decode('utf-8-sig').splitlines()),2)
    def test_method_restrictions(self):
        self.assertEqual(self.client.get('/api/sessions/').status_code,405)
        self.assertEqual(self.client.post('/api/history/').status_code,405)

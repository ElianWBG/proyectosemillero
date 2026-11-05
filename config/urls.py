from django.urls import path
from counter import views
urlpatterns=[path('',views.index,name='index'),path('api/sessions/',views.start,name='start'),path('api/sessions/<uuid:pk>/frame/',views.frame,name='frame'),path('api/sessions/<uuid:pk>/stop/',views.stop,name='stop'),path('api/history/',views.history,name='history'),path('api/sessions/<uuid:pk>/export/',views.export_csv,name='export')]

from pathlib import Path
import os
from dotenv import load_dotenv
BASE_DIR=Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR/'.env')
SECRET_KEY=os.environ.get('DJANGO_SECRET_KEY','')
if not SECRET_KEY:
    raise RuntimeError('Falta DJANGO_SECRET_KEY. Ejecute python configurar.py primero.')
DEBUG=os.environ.get('DJANGO_DEBUG','0')=='1'
ALLOWED_HOSTS=os.environ.get('DJANGO_ALLOWED_HOSTS','localhost,127.0.0.1,testserver').split(',')
INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.sessions','django.contrib.staticfiles','counter']
MIDDLEWARE=['django.middleware.security.SecurityMiddleware','django.contrib.sessions.middleware.SessionMiddleware','django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware','django.middleware.clickjacking.XFrameOptionsMiddleware']
ROOT_URLCONF='config.urls'
TEMPLATES=[{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[BASE_DIR/'templates'],'APP_DIRS':True,'OPTIONS':{'context_processors':['django.template.context_processors.request','django.template.context_processors.static']}}]
WSGI_APPLICATION='config.wsgi.application'
DATABASES={'default':{'ENGINE':'django.db.backends.postgresql','NAME':os.environ.get('POSTGRES_DB','visorlab'),'USER':os.environ.get('POSTGRES_USER','visorlab'),'PASSWORD':os.environ.get('POSTGRES_PASSWORD',''),'HOST':os.environ.get('POSTGRES_HOST','127.0.0.1'),'PORT':os.environ.get('POSTGRES_PORT','5432'),'CONN_MAX_AGE':0,'OPTIONS':{'connect_timeout':5}}}
if os.environ.get('POSTGRES_TEST_DB'):
    DATABASES['default']['TEST']={'NAME':os.environ['POSTGRES_TEST_DB']}
LANGUAGE_CODE='es';TIME_ZONE='America/Guayaquil';USE_I18N=True;USE_TZ=True
STATIC_URL='/static/';STATICFILES_DIRS=[BASE_DIR/'static'];STATIC_ROOT=BASE_DIR/'staticfiles'
DEFAULT_AUTO_FIELD='django.db.models.BigAutoField'
DATA_UPLOAD_MAX_MEMORY_SIZE=3*1024*1024
FILE_UPLOAD_MAX_MEMORY_SIZE=2*1024*1024
SESSION_COOKIE_HTTPONLY=True;SESSION_COOKIE_SAMESITE='Lax'
SECURE_CONTENT_TYPE_NOSNIFF=True;X_FRAME_OPTIONS='DENY'

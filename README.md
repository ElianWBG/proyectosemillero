# VisorLab
Conteo de personas con Django, OpenCV y PostgreSQL.

## Ejecutar con Docker

```sh
python configurar.py
docker compose up --build
```

Abrir http://localhost:8000 y permitir la cámara del computador.

## Ejecutar sin Docker

Python3.12 y PostgreSQL14 o superior.

```sh
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python configurar.py
```

Crear una base PostgreSQL vacía y colocar sus datos de conexión en `.env`.

```sh
.venv/Scripts/python manage.py migrate
.venv/Scripts/python manage.py runserver 127.0.0.1:8000
```

En Linux o macOS usar `.venv/bin/python`. No subir `.env` ni `.venv`.

## Pruebas

```sh
python manage.py test counter --keepdb
node --test tests/*.test.cjs
```

Con Docker: `docker compose exec web python manage.py test counter --keepdb`.
El usuario de pruebas necesita permiso para crear una base de prueba.

Rostros: YuNet preentrenado. Personas/cuerpos: YOLOX-S (OpenCV DNN), filtrado a la clase persona. Los identificadores son temporales; no identifican personas por nombre. Modelo y licencia original incluidos en `counter/assets/`. La precisión depende de iluminación, encuadre y oclusiones. No se almacenan imágenes ni video de las sesiones.


## Detector de personas

El modo Cuerpos y el modo Mixto utilizan YOLOX-S de OpenCV Zoo. El modelo ONNX y su licencia Apache 2.0 se incluyen en `counter/assets`; no se descarga nada al iniciar. No requiere instalar PyTorch ni Ultralytics.

Confianza inicial: 35%; sensible: 20%; exploratoria: 10%; estricta: 60%. Una confianza menor puede aumentar falsos positivos. Para cambiarla, guarde o descarte el resultado pendiente y vuelva a cargar la imagen. El modelo puede detectar personas parcialmente encuadradas, pero no garantiza detectar a todas. En CPU el procesamiento puede tardar alrededor de un segundo o m?s por fotograma; no se garantiza video fluido.
